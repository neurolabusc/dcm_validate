// JPEG-LS encoder for frame-decoder fixtures that dcmcjpls cannot write: interleave mode
// None (planar RGB). Uses the installed CharLS 2.
// Usage: encode_jls <width> <height> <components> <bits> <interleave 0|1|2> <near> <in.raw> <out.jls>
// in.raw: samples as uint8 (bits <= 8) or little-endian uint16, planar for interleave 0, else interleaved.
#include <cstdio>
#include <cstdlib>
#include <vector>
#include "charls/charls.h"

int main(int argc, char **argv) {
	if (argc != 9) {
		fprintf(stderr, "usage: %s <w> <h> <comps> <bits> <ilv> <near> <in.raw> <out.jls>\n", argv[0]);
		return 2;
	}
	JlsParameters p = {};
	p.width = atoi(argv[1]);
	p.height = atoi(argv[2]);
	p.components = atoi(argv[3]);
	p.bitsPerSample = atoi(argv[4]);
	p.interleaveMode = (charls::InterleaveMode)atoi(argv[5]);
	p.allowedLossyError = atoi(argv[6]);
	FILE *f = fopen(argv[7], "rb");
	if (!f) return 1;
	std::vector<unsigned char> in;
	unsigned char tmp[65536];
	size_t n;
	while ((n = fread(tmp, 1, sizeof(tmp), f)) > 0) in.insert(in.end(), tmp, tmp + n);
	fclose(f);
	std::vector<unsigned char> out(in.size() * 2 + 1024);
	size_t written = 0;
	if (JpegLsEncode(out.data(), out.size(), &written, in.data(), in.size(), &p, nullptr) != charls::ApiResult::OK) {
		fprintf(stderr, "CharLS encode failed\n");
		return 1;
	}
	f = fopen(argv[8], "wb");
	fwrite(out.data(), 1, written, f);
	fclose(f);
	return 0;
}
