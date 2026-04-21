"""Unit tests for ML components."""

import pytest
from ml_service.dtw_scorer import score_window, get_qualitative_label

def test_dtw_perfect_match():
    # Identical windows should have distance 0 and score ~100
    window = [{"elbow_angle_left": 1.0, "torso_rotation": 0.5} for _ in range(30)]
    score = score_window(window, window)
    assert score == 100.0

def test_qualitative_labels():
    assert get_qualitative_label(90) == "elite"
    assert get_qualitative_label(75) == "good"
    assert get_qualitative_label(60) == "developing"
    assert get_qualitative_label(40) == "poor"
