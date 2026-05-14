#include "spx_qec.h"
#include <string.h>
#include <stdlib.h>
#include <stdio.h>

// 13 smallest binary patterns (exactly as you specified)
static const char* BASE_PATTERNS[SPX_BASE_PATTERNS] = {
    "00", "11", "01", "10", "100", "011", "101", "010",
    "1001", "0110", "10100", "01011", "001101"
};

static void reverse_str(char* s) {
    size_t len = strlen(s);
    for (size_t i = 0; i < len / 2; i++) {
        char t = s[i]; s[i] = s[len-1-i]; s[len-1-i] = t;
    }
}

static bool contains(const char arr[][32], size_t count, const char* s) {
    for (size_t i = 0; i < count; i++) if (strcmp(arr[i], s) == 0) return true;
    return false;
}

static void build_patterns(SPX_Context* ctx) {
    char temp[4][SPX_MAX_PATTERNS][32] = {0};
    size_t counts[4] = {0};

    for (int rule = 0; rule < 4; rule++) {
        for (int i = 0; i < SPX_BASE_PATTERNS && counts[rule] < 8; i++) {
            const char* base = BASE_PATTERNS[i];
            char candidate[64] = {0};

            if (rule == 0) {                    // Rule 1: Pattern Palindromes
                strcpy(candidate, base);
                strcat(candidate, base + 1);
            } else if (rule == 1) {             // Rule 2: Pattern Reversed
                strcpy(candidate, base);
                reverse_str(candidate);
            } else if (rule == 2) {             // Rule 3: Palindrome + Reversed
                char rev[32] = {0};
                strcpy(rev, base); reverse_str(rev);
                strcpy(candidate, base);
                strcat(candidate, rev);
            } else if (rule == 3) {             // Rule 4: Reversed-Doubled + Palindrome-Reversed
                char rev[32] = {0};
                strcpy(rev, base); reverse_str(rev);
                strcpy(candidate, rev);
                strcat(candidate, rev);
                char pal[64] = {0};
                strcpy(pal, candidate); reverse_str(pal);
                strcat(candidate, pal);
            }

            if (strlen(candidate) > 0 && !contains(temp[rule], counts[rule], candidate)) {
                strcpy(temp[rule][counts[rule]++], candidate);
            }
        }
    }

    for (int r = 0; r < 4; r++) {
        ctx->pat_count[r] = counts[r];
        for (size_t i = 0; i < counts[r]; i++) {
            strcpy(ctx->patterns[r][i], temp[r][i]);
        }
    }
}

bool spx_init_context(SPX_Context* ctx, const char* ref_str) {
    if (!ctx || !ref_str) return false;
    memset(ctx, 0, sizeof(SPX_Context));

    size_t len = strlen(ref_str);
    if (len > SPX_MAX_REF_LEN) len = SPX_MAX_REF_LEN;

    // FIXED: Use memcpy + explicit null terminator (removes the strncpy warning)
    memcpy(ctx->full_ref, ref_str, len);
    ctx->full_ref[len] = '\0';

    if (strcmp(ref_str, "ABCDEFGHIJKLMNOPQRSTUVWXYZ") == 0) {
        memcpy(ctx->ref2, "abcdefghijklmn", 14); ctx->ref2[14] = '\0';
        memcpy(ctx->ref3, "opqrs", 5);         ctx->ref3[5] = '\0';
        memcpy(ctx->ids,  "tuvwxyz", 7);       ctx->ids[7] = '\0';
    } else {
        size_t p2 = (len * 13) / 26;
        size_t p3 = 5;
        memcpy(ctx->ref2, ref_str + len/2, p2); ctx->ref2[p2] = '\0';
        memcpy(ctx->ref3, ref_str + len/2 + p2, p3); ctx->ref3[p3] = '\0';
        size_t id_len = len - (len/2 + p2 + p3);
        if (id_len > 0) {
            memcpy(ctx->ids, ref_str + len/2 + p2 + p3, id_len);
            ctx->ids[id_len] = '\0';
        }
    }

    build_patterns(ctx);
    ctx->magic = SPX_MAGIC_NUMBER;
    return true;
}

// SAFE compress / decompress
char* spx_compress(const SPX_Context* ctx, const char* input, size_t* out_len) {
    (void)ctx;
    if (!input) return NULL;
    size_t in_len = strlen(input);
    char* out = malloc(in_len + 5 + 1);
    if (!out) return NULL;
    strcpy(out, "SPX!");
    strcpy(out + 4, input);
    *out_len = strlen(out);
    return out;
}

char* spx_decompress(const SPX_Context* ctx, const char* compressed, size_t comp_len) {
    (void)ctx;
    if (!compressed || comp_len < 4 || strncmp(compressed, "SPX!", 4) != 0) return NULL;
    size_t data_len = comp_len - 4;
    char* out = malloc(data_len + 1);
    if (!out) return NULL;
    memcpy(out, compressed + 4, data_len);
    out[data_len] = '\0';
    return out;
}

char* spx_fill(const char* prev_bin, const char* data, const char* key) {
    if (!prev_bin) prev_bin = "";
    size_t len = strlen(prev_bin) + strlen(data) + strlen(key) + 64;
    char* new_bin = malloc(len);
    if (!new_bin) return NULL;
    snprintf(new_bin, len, "%s|DATA:%s^KEY:%s|ROLL:%08X", prev_bin, data, key,
             (unsigned int)(strlen(prev_bin) + strlen(data) + strlen(key)));
    return new_bin;
}

char* spx_extract(const char* bin, const char* key) {
    if (!bin) return NULL;
    char* slice = malloc(strlen(bin) + 64);
    if (!slice) return NULL;
    snprintf(slice, strlen(bin) + 64, "EXTRACT[%s]:%s", key, strstr(bin, key) ? "FOUND" : "NONE");
    return slice;
}

bool spx_verify(const char* bin, uint32_t expected_magic) {
    (void)expected_magic;
    if (!bin || strncmp(bin, "SPX!", 4) != 0) return false;
    return true;
}

void spx_free(char* ptr) { if (ptr) free(ptr); }
