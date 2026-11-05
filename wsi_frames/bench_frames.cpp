// Timing harness for dcm2niix's frame decoders (nii_decodeFrameRGBA / nii_decodeFrame).
// Usage: bench_frames <rgba|samples> <reps> <photometric> <in> [<in> ...]
// Reads every input once, then decodes them all <reps> times; prints ms per frame.
#include <chrono>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <vector>
#include "nii_dicom.h"

int main(int argc, char **argv) {
	if (argc < 5) {
		fprintf(stderr, "usage: %s <rgba|samples> <reps> <photometric> <in> [...]\n", argv[0]);
		return 2;
	}
	bool rgba = strcmp(argv[1], "rgba") == 0;
	int reps = atoi(argv[2]);
	std::vector<std::vector<unsigned char>> frames;
	for (int i = 4; i < argc; i++) {
		FILE *f = fopen(argv[i], "rb");
		if (!f) return 1;
		std::vector<unsigned char> buf;
		unsigned char tmp[65536];
		size_t n;
		while ((n = fread(tmp, 1, sizeof(tmp), f)) > 0) buf.insert(buf.end(), tmp, tmp + n);
		fclose(f);
		frames.push_back(buf);
	}
	auto t0 = std::chrono::steady_clock::now();
	for (int r = 0; r < reps; r++)
		for (auto &b : frames) {
			struct TFrameInfo info;
#ifdef BENCH_RGBA_ONLY
			void *out = nii_decodeFrameRGBA(b.data(), b.size(), argv[3], &info); // the pre-P4 signature
#else
			void *out = rgba ? (void *)nii_decodeFrameRGBA(b.data(), b.size(), argv[3], 0, &info) : nii_decodeFrame(b.data(), b.size(), argv[3], &info);
#endif
			if (!out) return 1;
			free(out);
		}
	double ms = std::chrono::duration<double, std::milli>(std::chrono::steady_clock::now() - t0).count();
	printf("%.3f ms/frame (%zu frames x %d)\n", ms / (frames.size() * reps), frames.size(), reps);
	return 0;
}
