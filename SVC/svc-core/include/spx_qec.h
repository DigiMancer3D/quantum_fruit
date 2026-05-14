#pragma once
#include <stdint.h>
#include <stdbool.h>
#include <stddef.h>

#define SPX_MAX_REF_LEN     64
#define SPX_BASE_PATTERNS   13
#define SPX_MAX_PATTERNS    32
#define SPX_MAGIC_NUMBER    0x53505821  // "SPX!"

typedef struct {
    char full_ref[SPX_MAX_REF_LEN+1];
    char ref2[SPX_MAX_REF_LEN+1];
    char ref3[SPX_MAX_REF_LEN+1];
    char ids[SPX_MAX_REF_LEN+1];
    char patterns[4][SPX_MAX_PATTERNS][32];
    size_t pat_count[4];
    uint32_t magic;
} SPX_Context;

bool spx_init_context(SPX_Context* ctx, const char* ref_str);
char* spx_compress(const SPX_Context* ctx, const char* input, size_t* out_len);
char* spx_decompress(const SPX_Context* ctx, const char* compressed, size_t comp_len);
char* spx_fill(const char* prev_bin, const char* data, const char* key);
char* spx_extract(const char* bin, const char* key);
bool spx_verify(const char* bin, uint32_t expected_magic);
void spx_free(char* ptr);
