"""Generate the shared, reproducible input signal for both C filters."""

import csv
from pathlib import Path

import numpy as np


SAMPLE_RATE_HZ = 1000
DURATION_SECONDS = 2.0
LOW_FREQUENCY_HZ = 40.0
HIGH_FREQUENCY_HZ = 220.0
RANDOM_SEED = 2025
OUTPUT_PATH = Path(__file__).resolve().parents[1] / "results" / "generated" / "input.csv"


def main() -> None:
    sample_count = int(SAMPLE_RATE_HZ * DURATION_SECONDS)
    sample_indices = np.arange(sample_count)
    time_seconds = sample_indices / SAMPLE_RATE_HZ
    random_generator = np.random.default_rng(RANDOM_SEED)
    signal = (
        0.55 * np.sin(2 * np.pi * LOW_FREQUENCY_HZ * time_seconds)
        + 0.25 * np.sin(2 * np.pi * HIGH_FREQUENCY_HZ * time_seconds)
        + 0.03 * random_generator.standard_normal(sample_count)
    )

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT_PATH.open("w", newline="", encoding="utf-8") as csv_file:
        writer = csv.writer(csv_file)
        writer.writerow(["sample", "input"])
        writer.writerows((index, f"{value:.17g}") for index, value in enumerate(signal))

    print(f"Wrote {sample_count} samples to {OUTPUT_PATH}")
    print(
        f"Sampling rate: {SAMPLE_RATE_HZ} Hz; tones: "
        f"{LOW_FREQUENCY_HZ:g} Hz and {HIGH_FREQUENCY_HZ:g} Hz"
    )


if __name__ == "__main__":
    main()
