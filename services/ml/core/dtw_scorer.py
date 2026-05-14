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

DTW_FEATURE_ORDER: list[str] = [
    "elbow_angle_left",
    "forward_extent_left",
    "torso_rotation",
    "vertical_displacement",
    "knee_flexion",
    "weight_transfer",
    "hand_speed",
    "retraction_speed",
]

# Decay constant empirically validated
DTW_K: float = 10.0
WINDOW_SIZE = 30


# ── Internal helpers ─────────────────────────────────────────────────────────

def normalize_feature_vector(frame: dict) -> list[float]:
    """Single shared normalization function for DTW features."""
    row = []
    for key in DTW_FEATURE_ORDER:
        value = float(frame.get(key, 0.0))

        if key == "elbow_angle_left" or key == "knee_flexion":
            value /= 180.0
        elif key == "forward_extent_left" or key == "weight_transfer":
            value = (value + 0.5) # Shift to positive range [0, 1] roughly
        elif key == "torso_rotation":
            value /= 0.5 # Normalized by expected max rotation depth
        elif key == "vertical_displacement":
            value = (value + 0.2) / 0.5
        elif key == "hand_speed":
            value /= 15.0
        elif key == "retraction_speed":
            value /= 5.0

        row.append(float(value))
    return row

def _window_to_matrix(window: list[dict]) -> np.ndarray:
    """Convert a list of feature dicts to a (30, N) float32 array."""
    rows = [normalize_feature_vector(f) for f in window]
    return np.array(rows, dtype=np.float32)

def get_qualitative_label(score: float) -> str:
    if score >= 85: return "elite"
    if score >= 70: return "good"
    if score >= 50: return "developing"
    return "poor"


# ── Public API ────────────────────────────────────────────────────────────────

def score_window(window: list[dict], baseline: list[dict]) -> float:
    """Compute a similarity score (0–100) between *window* and *baseline*."""
    if len(window) < WINDOW_SIZE or len(baseline) < WINDOW_SIZE:
        return 0.0

    mat_window   = _window_to_matrix(window[:WINDOW_SIZE])
    mat_baseline = _window_to_matrix(baseline[:WINDOW_SIZE])

    distance = float(dtw_ndim.distance(mat_window, mat_baseline))
    score = 100.0 * math.exp(-distance / DTW_K)
    return float(np.clip(score, 0.0, 100.0))

def score_window_vs_multi_baseline(window: list[dict], baselines: list[list[dict]]) -> float:
    """Compute the maximum similarity score against a set of professional baselines.
    
    Implements: score = max(DTW(window, baseline_i))
    """
    if not baselines:
        return 100.0 # Cold start fallback
        
    scores = [score_window(window, b) for b in baselines]
    return max(scores) if scores else 0.0


def score_window_vs_self(window: list[dict]) -> float:  # noqa: ARG001
    """Return 100.0 — perfect score used when no baseline is loaded yet.

    This sentinel avoids gating inference behind a missing baseline during
    early sessions or cold-start scenarios.
    """
    return 100.0







