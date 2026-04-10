"""DTW-based similarity scoring for boxing technique windows.

Compares a 30-frame feature window against a reference (baseline) window
using multivariate Dynamic Time Warping (``dtaidistance.dtw_ndim``).

Score interpretation (boxing-domain-expert validated):
    >= 85  competition level
    70-84  functional technique
    50-69  specific error present
    < 50   invalid / severely incorrect

The exponential mapping ``100 * exp(-distance / DTW_K)`` ensures:
- A window identical to the baseline scores 100.
- The score degrades smoothly; the DTW_K constant controls sensitivity.
"""

from __future__ import annotations

import logging
import math

import numpy as np
from dtaidistance import dtw_ndim

logger = logging.getLogger(__name__)

FEATURE_ORDER: list[str] = [
    "elbow_angle_left",
    "elbow_angle_right",
    "forward_extent_left",
    "forward_extent_right",
    "shoulder_rotation",
    "hip_rotation",
    "guard_distance",
    "wrist_lateral_displacement",
]

DTW_FEATURE_ORDER: list[str] = [
    "elbow_angle_left",
    "forward_extent_left",
    "hand_speed",
    "retraction_speed",
]

# Decay constant empirically validated via test_dtw_scale.py
# K=10.0 provides good separation (Random ~36, Perturbed ~95)
DTW_K: float = 10.0

WINDOW_SIZE = 30  # frames — constraint C-03


# ── Internal helpers ─────────────────────────────────────────────────────────

def normalize_feature_vector(frame: dict) -> list[float]:
    """Single shared normalization function for DTW features.
    
    Transforms raw features into normalized [0,1] or similar scale.
    """
    row = []
    for key in DTW_FEATURE_ORDER:
        if key not in frame:
            logger.warning("Missing required feature key: %s. Defaulting to 0.0", key)
            value = 0.0
        else:
            value = float(frame[key])

        if key == "elbow_angle_left":
            value /= 180.0
        elif key == "forward_extent_left":
            pass # keep as is
        elif key == "hand_speed":
            value /= 15.0
        elif key == "retraction_speed":
            value /= 1.5

        row.append(value)
    return row

def _window_to_matrix(window: list[dict]) -> np.ndarray:
    """Convert a list of feature dicts to a (30, 4) float32 array."""
    rows = []
    for frame in window:
        rows.append(normalize_feature_vector(frame))
    return np.array(rows, dtype=np.float32)

def get_qualitative_label(score: float) -> str:
    if score >= 80:
        return "good"
    elif score >= 50:
        return "acceptable"
    else:
        return "poor"


# ── Public API ────────────────────────────────────────────────────────────────

def score_window(window: list[dict], baseline: list[dict]) -> float:
    """Compute a similarity score (0–100) between *window* and *baseline*.

    Uses multivariate DTW on (30, 8) float32 matrices.  Lower DTW distance
    maps to a higher score via the formula: ``100 * exp(-distance / DTW_K)``.

    Args:
        window:   30-frame feature window from the current athlete, oldest-first.
        baseline: 30-frame reference window from a professional athlete,
                  oldest-first.

    Returns:
        Float in [0, 100].  Returns 0.0 if either argument has fewer than 30
        frames (prevents partial-window comparisons).
    """
    if len(window) < WINDOW_SIZE:
        logger.warning("score_window failed: window length %d < %d", len(window), WINDOW_SIZE)
        return 0.0
    if len(baseline) < WINDOW_SIZE:
        logger.warning("score_window failed: baseline length %d < %d", len(baseline), WINDOW_SIZE)
        return 0.0

    # Phase 4 - Window Alignment Validation: ensure exact lengths for accurate alignment
    assert len(window) == WINDOW_SIZE, f"Expected {WINDOW_SIZE} frames in window, got {len(window)}"
    assert len(baseline) == WINDOW_SIZE, f"Expected {WINDOW_SIZE} frames in baseline, got {len(baseline)}"

    mat_window   = _window_to_matrix(window[:WINDOW_SIZE])
    mat_baseline = _window_to_matrix(baseline[:WINDOW_SIZE])

    distance = float(dtw_ndim.distance(mat_window, mat_baseline))
    score = 100.0 * math.exp(-distance / DTW_K)
    return float(np.clip(score, 0.0, 100.0))


def score_window_vs_self(window: list[dict]) -> float:  # noqa: ARG001
    """Return 100.0 — perfect score used when no baseline is loaded yet.

    This sentinel avoids gating inference behind a missing baseline during
    early sessions or cold-start scenarios.
    """
    return 100.0
