"""Random Forest punch classifier for 4-class punch detection.

Classifies 30-frame windows into one of: jab | cross | hook | null.

A two-stage gate ensures high precision:
  Stage 1 — RF classifier: max(P(jab|cross|hook)) >= 0.35 AND P(null) < 0.65
  Stage 2 — DTW gate: dtw_score >= 50 (only applied when stage 1 fires)

Both stages must pass for a punch label to be emitted.  Otherwise the
output is ("null", P(null)).

All inference runs synchronously on CPU.  The trained pipeline is exported
via joblib so startup loading is fast (no model compilation step).

Thresholds validated by boxing-domain-expert:
    PUNCH_PROB_THRESHOLD  = 0.35
    NULL_PROB_CEILING     = 0.65
    DTW_GATE_MINIMUM      = 50.0
"""

from __future__ import annotations

import logging
from pathlib import Path

import joblib
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from services.ml.core.dtw_scorer import DTW_FEATURE_ORDER

logger = logging.getLogger(__name__)

# ── Constants ─────────────────────────────────────────────────────────────────

PUNCH_CLASSES: list[str] = ["jab", "cross", "hook", "null"]

MODEL_PATH = Path(__file__).parent / "models" / "punch_classifier.joblib"

WINDOW_SIZE = 30          # frames — constraint C-03
N_FEATURES  = len(DTW_FEATURE_ORDER)  # 8

# Validated by boxing-domain-expert
PUNCH_PROB_THRESHOLD: float = 0.35
NULL_PROB_CEILING:    float = 0.65
DTW_GATE_MINIMUM:     float = 50.0


# ── Classifier ────────────────────────────────────────────────────────────────

class PunchClassifier:
    """Random Forest classifier wrapped in a sklearn Pipeline.

    Usage (inference)::

        from services.ml.models.punch_classifier import punch_classifier
        label, confidence = punch_classifier.classify(window, dtw_score=72.4)

    Usage (offline training)::

        clf = PunchClassifier()
        metrics = clf.train_and_save(X_windows, y_labels)
    """

    def __init__(self) -> None:
        self._pipeline: Pipeline | None = None
        self._class_index: dict[str, int] = {c: i for i, c in enumerate(PUNCH_CLASSES)}
        self._load_if_exists()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def classify(
        self,
        window: list[dict],
        dtw_score: float = 0.0,
    ) -> tuple[str, float]:
        """Classify a 30-frame window into a punch type.

        Two-stage gate:
          1. RF must predict a punch (not null) with sufficient confidence.
          2. DTW score must be >= DTW_GATE_MINIMUM.

        Args:
            window:    30-frame feature window, oldest-first.
            dtw_score: Similarity score from ``dtw_scorer.score_window``.
                       Pass 0.0 when no baseline is loaded (gate will block).

        Returns:
            Tuple of (punch_type, confidence) where punch_type is one of
            PUNCH_CLASSES and confidence is in [0, 1].
        """
        # Model not loaded: safe fallback.
        if self._pipeline is None:
            return ("null", 1.0)

        # Need exactly 30 frames to make a meaningful prediction.
        if len(window) < WINDOW_SIZE:
            return ("null", 1.0)

        features_1d = self._flatten_window(window).reshape(1, -1)

        # Raw class probabilities from the RF pipeline.
        proba = self._pipeline.predict_proba(features_1d)[0]  # shape: (n_classes,)

        # Map probabilities to labelled dict for clarity.
        classes = self._pipeline.classes_  # same order as RF was trained on
        prob_map: dict[str, float] = {cls: float(p) for cls, p in zip(classes, proba)}

        p_null = prob_map.get("null", 0.0)
        p_punch_max = max(
            prob_map.get("jab",   0.0),
            prob_map.get("cross", 0.0),
            prob_map.get("hook",  0.0),
        )

        # Stage 1 — classifier gate.
        stage1_pass = (p_punch_max >= PUNCH_PROB_THRESHOLD) and (p_null < NULL_PROB_CEILING)
        if not stage1_pass:
            return ("null", p_null)

        # Stage 2 — DTW gate.
        if dtw_score < DTW_GATE_MINIMUM:
            return ("null", p_null)

        # Both gates passed: return the highest-probability punch class.
        best_punch = max(
            ("jab",   prob_map.get("jab",   0.0)),
            ("cross", prob_map.get("cross", 0.0)),
            ("hook",  prob_map.get("hook",  0.0)),
            key=lambda t: t[1],
        )
        return best_punch

    def train_and_save(
        self,
        X: list[list[dict]],
        y: list[str],
    ) -> dict:
        """Train the classifier on labeled 30-frame windows and persist it.

        This method is intended for *offline* use only — never call it inside
        the request/response path (violates memory and latency constraints).

        Args:
            X: List of 30-frame windows; each window is a list[dict] as
               returned by ``WindowBuffer.push_frame``.
            y: Parallel list of ground-truth labels from PUNCH_CLASSES.

        Returns:
            Dict with training accuracy and top-5 feature importances::

                {
                    "train_accuracy": 0.97,
                    "top5_feature_importances": [(feature_name, importance), ...]
                }
        """
        X_flat = np.array([self._flatten_window(w) for w in X])
        y_arr  = np.array(y)

        pipeline = Pipeline([
            ("scaler", StandardScaler()),
            (
                "rf",
                RandomForestClassifier(
                    n_estimators=200,
                    max_depth=12,
                    random_state=42,
                    class_weight="balanced",
                ),
            ),
        ])
        pipeline.fit(X_flat, y_arr)

        train_accuracy = float(pipeline.score(X_flat, y_arr))

        rf: RandomForestClassifier = pipeline.named_steps["rf"]
        importances = rf.feature_importances_
        feature_names = [
            f"{DTW_FEATURE_ORDER[i % N_FEATURES]}_f{i // N_FEATURES}"
            for i in range(WINDOW_SIZE * N_FEATURES)
        ]
        sorted_pairs = sorted(
            zip(feature_names, importances),
            key=lambda t: t[1],
            reverse=True,
        )
        top5 = sorted_pairs[:5]

        # Persist to disk.
        MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
        joblib.dump(pipeline, MODEL_PATH)
        logger.info("Punch classifier saved to %s", MODEL_PATH)

        self._pipeline = pipeline

        return {
            "train_accuracy": train_accuracy,
            "top5_feature_importances": top5,
        }

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _load_if_exists(self) -> None:
        """Load a previously trained pipeline from MODEL_PATH if present."""
        if MODEL_PATH.exists():
            try:
                self._pipeline = joblib.load(MODEL_PATH)
                logger.info("Punch classifier loaded from %s", MODEL_PATH)
            except Exception as exc:  # noqa: BLE001
                logger.warning("Could not load punch classifier: %s", exc)
                self._pipeline = None

    def _flatten_window(self, window: list[dict]) -> np.ndarray:
        """Flatten a 30-frame window into a 1-D feature vector (240 values).

        Elbow angles are normalised by /180 before flattening so all values
        are on a comparable scale.  Column order follows DTW_FEATURE_ORDER so the
        layout is consistent with ``dtw_scorer._window_to_matrix``.
        """
        rows = []
        for frame in window[:WINDOW_SIZE]:
            row = []
            for key in DTW_FEATURE_ORDER:
                value = float(frame.get(key, 0.0))
                if key in ("elbow_angle_left", "elbow_angle_right"):
                    value /= 180.0
                row.append(value)
            rows.append(row)

        # Pad with zeros if the window is shorter than WINDOW_SIZE.
        while len(rows) < WINDOW_SIZE:
            rows.append([0.0] * N_FEATURES)

        return np.array(rows, dtype=np.float32).flatten()


# ── Module-level singleton ────────────────────────────────────────────────────
# Loaded once at import time.  The same instance is shared across all
# WebSocket sessions; it is stateless after training so thread-safety is not
# a concern for inference.

punch_classifier = PunchClassifier()







