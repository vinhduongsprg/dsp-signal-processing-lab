#ifndef FIR_COMMON_H
#define FIR_COMMON_H

#include <ctype.h>
#include <errno.h>
#include <math.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define FIR_TAP_COUNT 31

static const double FIR_COEFFICIENTS[FIR_TAP_COUNT] = {
    6.2264927146063794e-19, 0.0012014263758827752, 0.0027843278479828914,
    0.0042273160854469005, 0.0039427634127764061, -2.412765926909971e-18,
    -0.0082567772926564822, -0.01858321013023596, -0.025389820435008304,
    -0.021235308698378589, 5.9929992378086381e-18, 0.039588112570909856,
    0.091888877020527657, 0.14509908103158412, 0.18490287856182103,
    0.1996606672986955, 0.18490287856182103, 0.14509908103158409,
    0.091888877020527671, 0.039588112570909863, 5.9929992378086404e-18,
    -0.021235308698378596, -0.025389820435008321, -0.018583210130235967,
    -0.008256777292656484, -2.412765926909971e-18, 0.0039427634127764044,
    0.0042273160854469022, 0.0027843278479828901, 0.0012014263758827752,
    6.2264927146063794e-19
};

static int read_signal_csv(const char *path, double **samples, size_t *count)
{
    FILE *file = fopen(path, "r");
    char line[256];
    size_t capacity = 0;
    int success = 0;

    *samples = NULL;
    *count = 0;
    if (file == NULL) {
        fprintf(stderr, "Cannot open input '%s': %s\n", path, strerror(errno));
        return 0;
    }

    if (fgets(line, sizeof(line), file) == NULL) {
        fprintf(stderr, "Input '%s' is empty or unreadable.\n", path);
        goto cleanup;
    }
    line[strcspn(line, "\r\n")] = '\0';
    if (strcmp(line, "sample,input") != 0) {
        fprintf(stderr, "Input '%s' must have the header sample,input.\n", path);
        goto cleanup;
    }

    while (fgets(line, sizeof(line), file) != NULL) {
        char *cursor = line;
        char *end = NULL;
        unsigned long long sample_index;
        double value;
        double *resized;

        if (strchr(line, '\n') == NULL && !feof(file)) {
            fprintf(stderr, "A row in '%s' exceeds the supported line length.\n", path);
            goto cleanup;
        }

        errno = 0;
        sample_index = strtoull(cursor, &end, 10);
        if (errno != 0 || end == cursor || *end != ',' ||
            sample_index != (unsigned long long)*count) {
            fprintf(stderr, "Invalid sample index or CSV row in '%s'.\n", path);
            goto cleanup;
        }

        cursor = end + 1;
        errno = 0;
        value = strtod(cursor, &end);
        if (errno != 0 || end == cursor || !isfinite(value)) {
            fprintf(stderr, "Invalid numeric input in '%s'.\n", path);
            goto cleanup;
        }
        while (*end != '\0' && isspace((unsigned char)*end)) {
            end++;
        }
        if (*end != '\0') {
            fprintf(stderr, "Unexpected data in a row of '%s'.\n", path);
            goto cleanup;
        }

        if (*count == capacity) {
            size_t new_capacity = capacity == 0 ? 256 : capacity * 2;
            if (new_capacity < capacity ||
                new_capacity > SIZE_MAX / sizeof(**samples)) {
                fprintf(stderr, "Input '%s' is too large to load.\n", path);
                goto cleanup;
            }
            resized = realloc(*samples, new_capacity * sizeof(**samples));
            if (resized == NULL) {
                fprintf(stderr, "Not enough memory to load '%s'.\n", path);
                goto cleanup;
            }
            *samples = resized;
            capacity = new_capacity;
        }
        (*samples)[(*count)++] = value;
    }

    if (ferror(file)) {
        fprintf(stderr, "Error reading input '%s'.\n", path);
        goto cleanup;
    }
    if (*count == 0) {
        fprintf(stderr, "Input '%s' contains no samples.\n", path);
        goto cleanup;
    }
    success = 1;

cleanup:
    if (fclose(file) != 0) {
        fprintf(stderr, "Error closing input '%s'.\n", path);
        success = 0;
    }
    if (!success) {
        free(*samples);
        *samples = NULL;
        *count = 0;
    }
    return success;
}

static int write_signal_csv(const char *path, const double *samples, size_t count)
{
    FILE *file = fopen(path, "w");
    size_t i;
    int success = 1;

    if (file == NULL) {
        fprintf(stderr, "Cannot open output '%s': %s\n", path, strerror(errno));
        return 0;
    }
    if (fprintf(file, "sample,value\n") < 0) {
        success = 0;
    }
    for (i = 0; success && i < count; i++) {
        if (fprintf(file, "%zu,%.17g\n", i, samples[i]) < 0) {
            success = 0;
        }
    }
    if (fclose(file) != 0) {
        success = 0;
    }
    if (!success) {
        fprintf(stderr, "Error writing output '%s'.\n", path);
    }
    return success;
}

#endif
