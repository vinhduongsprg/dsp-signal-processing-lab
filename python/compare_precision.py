"""Compare floating-point and Q15 FIR outputs and save their error plot."""

import csv
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

from precision_metrics import calculate_metrics


PROJECT_ROOT = Path(__file__).resolve().parents[1]
GENERATED_DIR = PROJECT_ROOT / "results" / "generated"
FLOAT_PATH = GENERATED_DIR / "filtered_float.csv"
Q15_PATH = GENERATED_DIR / "filtered_q15.csv"
PLOT_PATH = PROJECT_ROOT / "results" / "precision_comparison.png"


def load_output(path: Path) -> np.ndarray:
    if not path.is_file():
        raise FileNotFoundError(f"Required CSV file not found: {path}")

    values = []
    with path.open(newline="", encoding="utf-8") as csv_file:
        reader = csv.DictReader(csv_file)
        if not reader.fieldnames or not {"sample", "value"}.issubset(reader.fieldnames):
            raise ValueError(f"{path} must contain sample and value columns.")
        for expected_index, row in enumerate(reader):
            if int(row["sample"]) != expected_index:
                raise ValueError(f"Non-sequential sample index in {path}.")
            values.append(float(row["value"]))
    if not values:
        raise ValueError(f"No samples found in {path}.")
    return np.asarray(values, dtype=np.float64)


def main() -> None:
    floating_point = load_output(FLOAT_PATH)
    q15 = load_output(Q15_PATH)
    if floating_point.size != q15.size:
        raise ValueError("Floating-point and Q15 outputs must have the same sample count.")

    difference = floating_point - q15
    absolute_difference = np.abs(difference)
    metrics = calculate_metrics(floating_point, q15)

    sample_indices = np.arange(floating_point.size)
    figure, axes = plt.subplots(3, 1, figsize=(10, 8), sharex=True)
    axes[0].plot(sample_indices, floating_point, label="Floating point", linewidth=1)
    axes[0].set_ylabel("Amplitude")
    axes[0].set_title("Floating-point FIR output")
    axes[0].legend()
    axes[1].plot(sample_indices, q15, color="tab:orange", label="Q15", linewidth=1)
    axes[1].set_ylabel("Amplitude")
    axes[1].set_title("Q15 FIR output")
    axes[1].legend()
    axes[2].plot(sample_indices, absolute_difference, color="tab:red")
    axes[2].set(title="Absolute sample-by-sample difference", xlabel="Sample index",
                ylabel="Absolute error")
    for axis in axes:
        axis.grid(True, alpha=0.3)
    figure.tight_layout()
    PLOT_PATH.parent.mkdir(parents=True, exist_ok=True)
    figure.savefig(PLOT_PATH, dpi=160)
    plt.close(figure)

    print(f"MSE: {metrics['mse']:.12g}")
    print(f"RMSE: {metrics['rmse']:.12g}")
    print(f"Relative RMSE: {metrics['relative_rmse']:.6%}")
    print(f"SNR: {metrics['snr_db']:.6f} dB")
    print(f"Maximum absolute error: {metrics['maximum_absolute_error']:.12g}")
    print(f"Wrote {PLOT_PATH}")


if __name__ == "__main__":
    main()
