"""Measure Q15 FIR error and saturation over reproducible input amplitudes."""

import csv
import re
import subprocess
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

from precision_metrics import calculate_metrics
from signal_generator import generate_signal


PROJECT_ROOT = Path(__file__).resolve().parents[1]
GENERATED_DIR = PROJECT_ROOT / "results" / "generated"
SUMMARY_PATH = GENERATED_DIR / "amplitude_sensitivity.csv"
PLOT_PATH = PROJECT_ROOT / "results" / "amplitude_sensitivity.png"
FLOAT_EXECUTABLE = PROJECT_ROOT / "fir_filter.exe"
Q15_EXECUTABLE = PROJECT_ROOT / "fir_q15.exe"
AMPLITUDE_SCALES = (0.1, 0.25, 0.5, 0.75, 1.0, 1.25, 1.5)
SATURATION_PATTERN = re.compile(
    r"Q15 saturation events: input=(\d+), coefficients=(\d+), output=(\d+)"
)


def write_signal(path: Path, signal: np.ndarray) -> None:
    with path.open("w", newline="", encoding="utf-8") as csv_file:
        writer = csv.writer(csv_file)
        writer.writerow(["sample", "input"])
        writer.writerows(
            (index, f"{value:.17g}") for index, value in enumerate(signal)
        )


def load_output(path: Path) -> np.ndarray:
    values = []
    with path.open(newline="", encoding="utf-8") as csv_file:
        reader = csv.DictReader(csv_file)
        if not reader.fieldnames or not {"sample", "value"}.issubset(reader.fieldnames):
            raise ValueError(f"{path} must contain sample and value columns.")
        for expected_index, row in enumerate(reader):
            if int(row["sample"]) != expected_index:
                raise ValueError(f"Non-sequential sample index in {path}.")
            value = float(row["value"])
            if not np.isfinite(value):
                raise ValueError(f"Non-finite output value in {path}.")
            values.append(value)
    if not values:
        raise ValueError(f"No samples found in {path}.")
    return np.asarray(values, dtype=np.float64)


def run_filter(executable: Path, input_path: Path, output_path: Path) -> str:
    if not executable.is_file():
        raise FileNotFoundError(
            f"Required C executable not found: {executable}. "
            "Compile both filters using the README instructions first."
        )
    result = subprocess.run(
        [str(executable), str(input_path), str(output_path)],
        capture_output=True,
        check=False,
        text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(
            f"{executable.name} failed with exit code {result.returncode}:\n"
            f"{result.stderr.strip()}"
        )
    return result.stderr


def read_saturations(stderr: str) -> tuple[int, int, int]:
    match = SATURATION_PATTERN.search(stderr)
    if match is None:
        raise ValueError(f"Could not read Q15 saturation counts from: {stderr!r}")
    input_count, coefficient_count, output_count = (
        int(value) for value in match.groups()
    )
    return input_count, coefficient_count, output_count


def main() -> None:
    GENERATED_DIR.mkdir(parents=True, exist_ok=True)
    base_signal = generate_signal()
    rows = []

    for scale in AMPLITUDE_SCALES:
        input_path = GENERATED_DIR / f"sensitivity_input_{scale:g}.csv"
        float_path = GENERATED_DIR / f"sensitivity_float_{scale:g}.csv"
        q15_path = GENERATED_DIR / f"sensitivity_q15_{scale:g}.csv"
        write_signal(input_path, base_signal * scale)

        run_filter(FLOAT_EXECUTABLE, input_path, float_path)
        q15_stderr = run_filter(Q15_EXECUTABLE, input_path, q15_path)
        floating_point = load_output(float_path)
        q15 = load_output(q15_path)
        metrics = calculate_metrics(floating_point, q15)
        if floating_point.size != base_signal.size or q15.size != base_signal.size:
            raise ValueError("Filter output sample counts do not match the generated input.")
        input_saturations, coefficient_saturations, output_saturations = (
            read_saturations(q15_stderr)
        )
        rows.append({
            "amplitude_scale": scale,
            "input_peak": float(np.max(np.abs(base_signal * scale))),
            **metrics,
            "input_saturations": input_saturations,
            "coefficient_saturations": coefficient_saturations,
            "output_saturations": output_saturations,
        })

    fieldnames = list(rows[0])
    with SUMMARY_PATH.open("w", newline="", encoding="utf-8") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    scales = [row["amplitude_scale"] for row in rows]
    relative_rmse_percent = [100 * row["relative_rmse"] for row in rows]
    figure, axes = plt.subplots(2, 1, figsize=(9, 7), sharex=True)
    axes[0].plot(scales, relative_rmse_percent, marker="o", color="tab:blue")
    axes[0].set_ylabel("Relative RMSE (%)")
    axes[0].set_title("Q15 precision versus input amplitude")
    axes[0].set_yscale("log")
    axes[0].grid(True, alpha=0.3)
    axes[1].plot(
        scales, [row["input_saturations"] for row in rows],
        marker="o", label="Input", color="tab:orange")
    axes[1].plot(
        scales, [row["output_saturations"] for row in rows],
        marker="s", label="Output", color="tab:red")
    axes[1].set(xlabel="Input amplitude scale", ylabel="Saturation events")
    axes[1].grid(True, alpha=0.3)
    axes[1].legend()
    figure.tight_layout()
    figure.savefig(PLOT_PATH, dpi=160)
    plt.close(figure)

    print("Q15 amplitude sensitivity (same seeded signal, frequencies, and FIR taps):")
    print(
        "scale   rel_RMSE(%)    SNR(dB)      max_abs_error  "
        "input_sat  coefficient_sat  output_sat"
    )
    for row in rows:
        print(
            f"{row['amplitude_scale']:>5.2f}   "
            f"{100 * row['relative_rmse']:>11.6f}   "
            f"{row['snr_db']:>9.3f}   "
            f"{row['maximum_absolute_error']:>13.8g}   "
            f"{row['input_saturations']:>9}   "
            f"{row['coefficient_saturations']:>15}   "
            f"{row['output_saturations']:>10}"
        )
    print(f"Wrote {SUMMARY_PATH}")
    print(f"Wrote {PLOT_PATH}")


if __name__ == "__main__":
    main()
