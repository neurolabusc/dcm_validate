// Native harness for dcm2niix's nii_decodeFrameRGBA (DICOM-WSI tile decoder).
// Usage: decode_frames <photometric> <in.j2k> <out.ppm> [<in.j2k> <out.ppm> ...]
// Writes RGB PPMs (alpha must be 255 and is checked, not written) and prints one
// status line per frame: file status width height components bits mct isYCbCr.
#include <cstdio>
#include <cstdlib>
#include <vector>
#include "nii_dicom.h"

int main(int argc, char **argv) {
	if (argc < 4 || (argc - 2) % 2) {
		fprintf(stderr, "usage: %s <photometric> <in> <out.ppm> [...]\n", argv[0]);
		return 2;
	}
	int bad = 0;
	for (int i = 2; i + 1 < argc; i += 2) {
		FILE *f = fopen(argv[i], "rb");
		if (!f) { printf("%s open-failed\n", argv[i]); bad++; continue; }
		std::vector<unsigned char> buf;
		unsigned char tmp[65536];
		size_t n;
		while ((n = fread(tmp, 1, sizeof(tmp), f)) > 0) buf.insert(buf.end(), tmp, tmp + n);
		fclose(f);
		struct TFrameInfo info;
		unsigned char *rgba = nii_decodeFrameRGBA(buf.data(), buf.size(), argv[1], &info);
		printf("%s %d %d %d %d %d %d %d\n", argv[i], info.status, info.width, info.height, info.components, info.bitsStored, info.mct, info.isYCbCr);
		if (!rgba) { bad++; continue; }
		FILE *o = fopen(argv[i + 1], "wb");
		fprintf(o, "P6\n%d %d\n255\n", info.width, info.height);
		for (size_t p = 0; p < (size_t)info.width * info.height; p++) {
			if (rgba[4 * p + 3] != 255) { printf("%s alpha!=255 at %zu\n", argv[i], p); bad++; break; }
			fwrite(rgba + 4 * p, 1, 3, o);
		}
		fclose(o);
		free(rgba);
	}
	return bad ? 1 : 0;
}
