"""Analyze and plot the original and floating-point FIR-filtered signals."""

import csv
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

from signal_generator import SAMPLE_RATE_HZ


PROJECT_ROOT = Path(__file__).resolve().parents[1]
GENERATED_DIR = PROJECT_ROOT / "results" / "generated"
INPUT_PATH = GENERATED_DIR / "input.csv"
FLOAT_PATH = GENERATED_DIR / "filtered_float.csv"
Q15_PATH = GENERATED_DIR / "filtered_q15.csv"
TIME_PLOT_PATH = PROJECT_ROOT / "results" / "signal_comparison.png"
SPECTRUM_PLOT_PATH = PROJECT_ROOT / "results" / "frequency_spectrum.png"


def load_signal(path: Path, value_column: str) -> np.ndarray:
    if not path.is_file():
        raise FileNotFoundError(f"Required CSV file not found: {path}")

    with path.open(newline="", encoding="utf-8") as csv_file:
        reader = csv.DictReader(csv_file)
        if not reader.fieldnames or not {"sample", value_column}.issubset(reader.fieldnames):
            raise ValueError(f"{path} must contain sample and {value_column} columns.")
        values = []
        for expected_index, row in enumerate(reader):
            if int(row["sample"]) != expected_index:
                raise ValueError(f"Non-sequential sample index in {path}.")
            values.append(float(row[value_column]))
    if not values:
        raise ValueError(f"No samples found in {path}.")
    return np.asarray(values, dtype=np.float64)


def one_sided_amplitude(signal: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    window = np.hanning(signal.size)
    spectrum = np.fft.rfft(signal * window)
    amplitude = np.abs(spectrum) / np.sum(window)
    if signal.size % 2 == 0:
        amplitude[1:-1] *= 2
    else:
        amplitude[1:] *= 2
    frequencies = np.fft.rfftfreq(signal.size, d=1 / SAMPLE_RATE_HZ)
    return frequencies, amplitude


def report_dominant_frequencies(frequencies: np.ndarray, amplitude: np.ndarray) -> None:
    local_maxima = np.flatnonzero(
        (amplitude[1:-1] >= amplitude[:-2])
        & (amplitude[1:-1] > amplitude[2:])
    ) + 1
    local_maxima = local_maxima[frequencies[local_maxima] >= 5]
    strongest = local_maxima[np.argsort(amplitude[local_maxima])[-5:][::-1]]
    print("Strongest spectral peaks (frequency, one-sided amplitude):")
    for index in strongest:
        print(f"  {frequencies[index]:7.2f} Hz, {amplitude[index]:.6f}")


def main() -> None:
    original = load_signal(INPUT_PATH, "input")
    floating_point = load_signal(FLOAT_PATH, "value")
    q15 = load_signal(Q15_PATH, "value")
    if original.size != floating_point.size or original.size != q15.size:
        raise ValueError("Original and filtered signals must have the same sample count.")

    time_seconds = np.arange(original.size) / SAMPLE_RATE_HZ
    TIME_PLOT_PATH.parent.mkdir(parents=True, exist_ok=True)

    figure, axis = plt.subplots(figsize=(10, 4.5))
    displayed_samples = min(original.size, SAMPLE_RATE_HZ // 5)
    axis.plot(time_seconds[:displayed_samples], original[:displayed_samples],
              label="Original", linewidth=1)
    axis.plot(time_seconds[:displayed_samples], floating_point[:displayed_samples],
              label="FIR filtered (floating point)", linewidth=1.5)
    axis.plot(time_seconds[:displayed_samples], q15[:displayed_samples],
              label="FIR filtered (Q15)", linewidth=1, alpha=0.8)
    axis.set(title="Time-domain signal comparison", xlabel="Time (s)", ylabel="Amplitude")
    axis.grid(True, alpha=0.3)
    axis.legend()
    figure.tight_layout()
    figure.savefig(TIME_PLOT_PATH, dpi=160)
    plt.close(figure)

    frequencies, original_amplitude = one_sided_amplitude(original)
    _, floating_amplitude = one_sided_amplitude(floating_point)
    _, q15_amplitude = one_sided_amplitude(q15)
    figure, axes = plt.subplots(3, 1, figsize=(10, 9), sharex=True)
    spectrum_data = (
        ("Original signal", original_amplitude, "tab:blue"),
        ("Floating-point FIR output", floating_amplitude, "tab:orange"),
        ("Q15 FIR output", q15_amplitude, "tab:green"),
    )
    for axis, (title, amplitude, color) in zip(axes, spectrum_data):
        axis.plot(frequencies, amplitude, color=color)
        axis.set_title(title)
    for axis in axes:
        axis.set_ylabel("Amplitude")
        axis.set_xlim(0, SAMPLE_RATE_HZ / 2)
        axis.grid(True, alpha=0.3)
    axes[1].set_xlabel("Frequency (Hz)")
    figure.suptitle(
        f"One-sided amplitude spectra (FFT bin spacing: "
        f"{SAMPLE_RATE_HZ / original.size:.3f} Hz)"
    )
    figure.tight_layout()
    figure.savefig(SPECTRUM_PLOT_PATH, dpi=160)
    plt.close(figure)

    print(f"FFT bin spacing: {SAMPLE_RATE_HZ / original.size:.3f} Hz")
    print("Original signal:")
    report_dominant_frequencies(frequencies, original_amplitude)
    print("Floating-point filtered signal:")
    report_dominant_frequencies(frequencies, floating_amplitude)
    print("Q15 filtered signal:")
    report_dominant_frequencies(frequencies, q15_amplitude)
    print(f"Wrote {TIME_PLOT_PATH}")
    print(f"Wrote {SPECTRUM_PLOT_PATH}")


if __name__ == "__main__":
    main()
