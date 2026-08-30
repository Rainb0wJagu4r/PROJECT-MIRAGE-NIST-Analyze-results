#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <string.h>
#include "unif01.h"
#include "bbattery.h"
#include "ufile.h"

typedef struct {
    FILE *fp;
    size_t header_offset;
    int loop;
    uint64_t total_bytes_read;
} FileGenState;

static unsigned long file_get_bits(void *param, void *state) {
    FileGenState *s = (FileGenState*)state;
    uint32_t val = 0;
    size_t n = fread(&val, 1, sizeof(val), s->fp);
    if (n < sizeof(val)) {
        if (s->loop) {
            fseek(s->fp, (long)s->header_offset, SEEK_SET);
            fread(&val, 1, sizeof(val), s->fp);
        } else {
            return 0;
        }
    }
    s->total_bytes_read += sizeof(val);
    return (unsigned long)val;
}

static double file_get_u01(void *param, void *state) {
    return file_get_bits(param, state) * unif01_INV32;
}

static void file_write_state(void *state) {
    FileGenState *s = (FileGenState*)state;
    printf("Bytes read: %llu\n", (unsigned long long)s->total_bytes_read);
}

unif01_Gen* create_file_gen(const char *path, size_t header_offset, int loop) {
    FILE *fp = fopen(path, "rb");
    if (!fp) return NULL;
    if (header_offset > 0) {
        fseek(fp, (long)header_offset, SEEK_SET);
    }
    FileGenState *s = (FileGenState*)malloc(sizeof(FileGenState));
    s->fp = fp;
    s->header_offset = header_offset;
    s->loop = loop;
    s->total_bytes_read = 0;

    unif01_Gen *gen = (unif01_Gen*)malloc(sizeof(unif01_Gen));
    gen->state = s;
    gen->param = NULL;
    gen->name = (char*)path;
    gen->GetBits = file_get_bits;
    gen->GetU01 = file_get_u01;
    gen->Write = file_write_state;
    return gen;
}

void delete_file_gen(unif01_Gen *gen) {
    if (gen) {
        FileGenState *s = (FileGenState*)gen->state;
        if (s) {
            if (s->fp) fclose(s->fp);
            free(s);
        }
        free(gen);
    }
}

int main(int argc, char *argv[]) {
    if (argc < 3) {
        printf("Usage: %s <suite> <binary_file> [header_offset] [num_bits]\n", argv[0]);
        printf("Suites: smallcrush, crush, rabbit, alphabit, diehard, fips\n");
        return 1;
    }

    char *suite = argv[1];
    char *file = argv[2];
    size_t header_offset = 0;
    double nbits = 0;
    if (argc >= 4) {
        header_offset = (size_t)atol(argv[3]);
    }
    if (argc >= 5) {
        nbits = atof(argv[4]);
    }

    printf("========================================================\n");
    printf("         TestU01 Cryptographic Randomness Suite        \n");
    printf("========================================================\n");
    printf("Suite:         %s\n", suite);
    printf("Target File:   %s\n", file);
    printf("Header Offset: %zu bytes\n", header_offset);
    printf("========================================================\n\n");

    unif01_Gen *gen = create_file_gen(file, header_offset, 1);
    if (!gen) {
        printf("Error: Could not open file %s\n", file);
        return 1;
    }

    if (strcmp(suite, "smallcrush") == 0) {
        bbattery_SmallCrush(gen);
    } else if (strcmp(suite, "crush") == 0) {
        bbattery_Crush(gen);
    } else if (strcmp(suite, "diehard") == 0) {
        bbattery_pseudoDIEHARD(gen);
    } else if (strcmp(suite, "fips") == 0) {
        bbattery_FIPS_140_2(gen);
    } else if (strcmp(suite, "rabbit") == 0) {
        if (nbits <= 0) nbits = 10485760.0;
        bbattery_Rabbit(gen, nbits);
    } else if (strcmp(suite, "alphabit") == 0) {
        if (nbits <= 0) nbits = 10485760.0;
        bbattery_Alphabit(gen, nbits, 0, 32);
    } else {
        printf("Unknown suite: %s\n", suite);
        delete_file_gen(gen);
        return 1;
    }

    delete_file_gen(gen);
    printf("\nTest execution finished successfully.\n");
    return 0;
}
