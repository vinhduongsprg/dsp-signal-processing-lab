#include "fir_common.h"

static void apply_fir_filter(const double *input, double *output, size_t sample_count)
{
    size_t n;

    for (n = 0; n < sample_count; n++) {
        double accumulator = 0.0;
        size_t tap;

        /* y[n] = sum(h[k] * x[n-k]); unavailable pre-zero samples are omitted. */
        for (tap = 0; tap < FIR_TAP_COUNT && tap <= n; tap++) {
            accumulator += FIR_COEFFICIENTS[tap] * input[n - tap];
        }
        output[n] = accumulator;
    }
}

int main(int argc, char **argv)
{
    double *input = NULL;
    double *output = NULL;
    size_t sample_count = 0;
    int exit_code = EXIT_FAILURE;

    if (argc != 3) {
        fprintf(stderr, "Usage: %s <input.csv> <output.csv>\n", argv[0]);
        return EXIT_FAILURE;
    }
    if (!read_signal_csv(argv[1], &input, &sample_count)) {
        return EXIT_FAILURE;
    }
    output = malloc(sample_count * sizeof(*output));
    if (output == NULL) {
        fprintf(stderr, "Not enough memory for filtered output.\n");
        goto cleanup;
    }

    apply_fir_filter(input, output, sample_count);
    if (write_signal_csv(argv[2], output, sample_count)) {
        exit_code = EXIT_SUCCESS;
    }

cleanup:
    free(output);
    free(input);
    return exit_code;
}
