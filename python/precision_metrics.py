"""Shared fixed-point error metrics against a floating-point reference."""

import numpy as np


def calculate_metrics(reference: np.ndarray, candidate: np.ndarray) -> dict[str, float]:
    if reference.shape != candidate.shape or reference.size == 0:
        raise ValueError("Reference and candidate must have the same non-zero shape.")

    error = reference - candidate
    mse = float(np.mean(error**2))
    rmse = float(np.sqrt(mse))
    reference_rms = float(np.sqrt(np.mean(reference**2)))
    if reference_rms > 0.0:
        relative_rmse = rmse / reference_rms
        snr_db = float(10 * np.log10(reference_rms**2 / mse)) if mse else float("inf")
    else:
        relative_rmse = float("inf") if rmse else 0.0
        snr_db = float("-inf")
    return {
        "mse": mse,
        "rmse": rmse,
        "relative_rmse": relative_rmse,
        "maximum_absolute_error": float(np.max(np.abs(error))),
        "snr_db": snr_db,
    }
