import numpy as np


class FeedbackEngine:
    """Compara las métricas del usuario contra el baseline y genera mensajes."""

    def __init__(self, baseline_df=None):
        self.mean = None
        self.std = None
        self.set_baseline(baseline_df)

    def set_baseline(self, baseline_df):
        self.baseline = baseline_df
        if baseline_df is None or baseline_df.empty:
            self.mean = None
            self.std = None
            return

        numeric_cols = baseline_df.select_dtypes(include=[np.number])
        if numeric_cols.empty:
            self.mean = None
            self.std = None
            return

        self.mean = numeric_cols.mean()
        self.std = numeric_cols.std().replace(0, np.nan)

    def compare(self, user_features):
        if self.mean is None or user_features is None:
            return None

        required = ("elbow_angle", "forward_extent")
        if any(key not in user_features for key in required):
            return None

        elbow_delta = user_features["elbow_angle"] - self.mean["elbow_angle"]
        baseline_extent = self.mean["forward_extent"]

        reach_ratio = (
            user_features["forward_extent"] / baseline_extent
            if baseline_extent not in (0, np.nan)
            else 1.0
        )

        if abs(elbow_delta) > 15:
            return "Baja mas el codo en la extension."

        if reach_ratio < 0.7:
            return "Extiende mas el jab hacia adelante."

        return "Buena tecnica, sigue asi."
