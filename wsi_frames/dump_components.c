// Dump a JPEG 2000 codestream's decoded component planes, with no colour handling,
// as an independent reference for dcm2niix's tile decoder (check_frames.py does the
// upsampling and YCbCr conversion itself). OpenJPEG still decodes; nothing else is shared.
// Output: "<ncomp> <mct> <color_space>" then per component "<w> <h> <dx> <dy> <prec> <sgnd>",
// then each component's samples as little-endian int32.
// Usage: dump_components <in.j2k> <out.bin>
#include <stdio.h>
#include <stdlib.h>
#include "openjpeg.h"

int main(int argc, char **argv) {
	if (argc != 3) {
		fprintf(stderr, "usage: %s <in.j2k> <out.bin>\n", argv[0]);
		return 2;
	}
	FILE *f = fopen(argv[1], "rb");
	if (!f)
		return 1;
	unsigned char magic[2];
	if (fread(magic, 1, 2, f) != 2)
		return 1;
	fclose(f);
	opj_stream_t *s = opj_stream_create_default_file_stream(argv[1], OPJ_TRUE);
	opj_codec_t *c = opj_create_decompress((magic[0] == 0xFF && magic[1] == 0x4F) ? OPJ_CODEC_J2K : OPJ_CODEC_JP2);
	opj_dparameters_t p;
	opj_set_default_decoder_parameters(&p);
	opj_image_t *im = NULL;
	if (!opj_setup_decoder(c, &p) || !opj_read_header(s, c, &im) || !opj_decode(c, s, im) || !opj_end_decompress(c, s))
		return 1;
	opj_codestream_info_v2_t *ci = opj_get_cstr_info(c);
	FILE *o = fopen(argv[2], "wb");
	fprintf(o, "%u %u %d\n", im->numcomps, ci ? ci->m_default_tile_info.mct : 0, (int)im->color_space);
	for (unsigned k = 0; k < im->numcomps; k++)
		fprintf(o, "%u %u %u %u %u %u\n", im->comps[k].w, im->comps[k].h, im->comps[k].dx, im->comps[k].dy, im->comps[k].prec, im->comps[k].sgnd);
	for (unsigned k = 0; k < im->numcomps; k++)
		fwrite(im->comps[k].data, sizeof(int), (size_t)im->comps[k].w * im->comps[k].h, o);
	fclose(o);
	if (ci)
		opj_destroy_cstr_info(&ci);
	opj_image_destroy(im);
	opj_destroy_codec(c);
	opj_stream_destroy(s);
	return 0;
}
