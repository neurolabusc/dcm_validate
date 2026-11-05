// Native harness for dcm2niix's frame decoders (DICOM-WSI tiles).
// Usage: decode_frames [--samples] [--bits <bitsStored>] <photometric> <in> <out> [<in> <out> ...]
// Default: nii_decodeFrameRGBA, writing RGB PPMs (alpha must be 255 and is checked, not written);
// --bits passes DICOM BitsStored (default 0, unknown).
// --samples: nii_decodeFrame, writing the raw interleaved samples (uint8, or little-endian uint16).
// Prints one status line per frame: file status width height components bits mct isYCbCr.
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <vector>
#include "nii_dicom.h"

int main(int argc, char **argv) {
	int a = 1; // index of <photometric>
	bool samples = (argc > a) && (strcmp(argv[a], "--samples") == 0);
	if (samples)
		a++;
	int bits = 0;
	if ((argc > a + 1) && (strcmp(argv[a], "--bits") == 0)) {
		bits = atoi(argv[a + 1]);
		a += 2;
	}
	if (argc < a + 3 || (argc - a - 1) % 2) {
		fprintf(stderr, "usage: %s [--samples] [--bits <n>] <photometric> <in> <out> [...]\n", argv[0]);
		return 2;
	}
	int bad = 0;
	for (int i = a + 1; i + 1 < argc; i += 2) {
		FILE *f = fopen(argv[i], "rb");
		if (!f) { printf("%s open-failed\n", argv[i]); bad++; continue; }
		std::vector<unsigned char> buf;
		unsigned char tmp[65536];
		size_t n;
		while ((n = fread(tmp, 1, sizeof(tmp), f)) > 0) buf.insert(buf.end(), tmp, tmp + n);
		fclose(f);
		struct TFrameInfo info;
		unsigned char *out = samples ? (unsigned char *)nii_decodeFrame(buf.data(), buf.size(), argv[a], &info) : nii_decodeFrameRGBA(buf.data(), buf.size(), argv[a], bits, &info);
		printf("%s %d %d %d %d %d %d %d\n", argv[i], info.status, info.width, info.height, info.components, info.bitsStored, info.mct, info.isYCbCr);
		if (!out) { bad++; continue; }
		FILE *o = fopen(argv[i + 1], "wb");
		size_t npix = (size_t)info.width * info.height;
		if (samples)
			fwrite(out, 1, npix * info.components * (info.bitsStored > 8 ? 2 : 1), o);
		else {
			fprintf(o, "P6\n%d %d\n255\n", info.width, info.height);
			for (size_t p = 0; p < npix; p++) {
				if (out[4 * p + 3] != 255) { printf("%s alpha!=255 at %zu\n", argv[i], p); bad++; break; }
				fwrite(out + 4 * p, 1, 3, o);
			}
		}
		fclose(o);
		free(out);
	}
	return bad ? 1 : 0;
}
