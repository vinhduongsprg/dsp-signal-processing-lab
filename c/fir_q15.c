#include "fir_common.h"

#define Q15_SCALE 32768.0
#define Q15_MAX 32767
#define Q15_MIN (-32768)

static int16_t double_to_q15(double value, size_t *saturation_count)
{
    double scaled = value * Q15_SCALE;

    if (scaled > Q15_MAX) {
        (*saturation_count)++;
        return Q15_MAX;
    }
    if (scaled < Q15_MIN) {
        (*saturation_count)++;
        return Q15_MIN;
    }
    return (int16_t)round(scaled);
}

static int16_t q30_to_q15(int64_t accumulator, size_t *saturation_count)
{
    const int64_t rounding_offset = INT64_C(1) << 14;
    int64_t rounded = accumulator >= 0
        ? (accumulator + rounding_offset) / (INT64_C(1) << 15)
        : (accumulator - rounding_offset) / (INT64_C(1) << 15);

    if (rounded > Q15_MAX) {
        (*saturation_count)++;
        return Q15_MAX;
    }
    if (rounded < Q15_MIN) {
        (*saturation_count)++;
        return Q15_MIN;
    }
    return (int16_t)rounded;
}

static void apply_fir_filter_q15(
    const double *input,
    double *output,
    size_t sample_count,
    size_t *input_saturations,
    size_t *coefficient_saturations,
    size_t *output_saturations)
{
    int16_t coefficients[FIR_TAP_COUNT];
    size_t tap;
    size_t n;

    for (tap = 0; tap < FIR_TAP_COUNT; tap++) {
        coefficients[tap] = double_to_q15(
            FIR_COEFFICIENTS[tap], coefficient_saturations);
    }

    for (n = 0; n < sample_count; n++) {
        int64_t accumulator = 0;
        size_t input_tap;

        for (input_tap = 0; input_tap < FIR_TAP_COUNT && input_tap <= n; input_tap++) {
            int16_t input_q15 = double_to_q15(
                input[n - input_tap], input_saturations);
            accumulator += (int32_t)input_q15 * coefficients[input_tap];
        }

        output[n] = (double)q30_to_q15(accumulator, output_saturations) / Q15_SCALE;
    }
}

int main(int argc, char **argv)
{
    double *input = NULL;
    double *output = NULL;
    size_t sample_count = 0;
    size_t input_saturations = 0;
    size_t coefficient_saturations = 0;
    size_t output_saturations = 0;
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

    apply_fir_filter_q15(
        input, output, sample_count,
        &input_saturations, &coefficient_saturations, &output_saturations);
    fprintf(stderr,
        "Q15 saturation events: input=%zu, coefficients=%zu, output=%zu\n",
        input_saturations, coefficient_saturations, output_saturations);
    if (write_signal_csv(argv[2], output, sample_count)) {
        exit_code = EXIT_SUCCESS;
    }

cleanup:
    free(output);
    free(input);
    return exit_code;
}
