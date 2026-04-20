import numpy as np
import logging

logger = logging.getLogger(__name__)

class FeedbackEngine:
    """Intelligent coaching engine for real-time boxing technique feedback.
    
    Compares user feature windows against professional baselines to identify
    specific biomechanical errors (speed drops, lack of rotation, poor retraction).
    """

    def __init__(self, baseline_df=None):
        self.baseline_stats = None
        self.set_baseline(baseline_df)

    def set_baseline(self, baseline_df):
        if baseline_df is None or baseline_df.empty:
            self.baseline_stats = None
            return

        numeric_cols = baseline_df.select_dtypes(include=[np.number])
        self.baseline_stats = {
            "mean": numeric_cols.mean().to_dict(),
            "std": numeric_cols.std().replace(0, 0.001).to_dict()
        }

    def analyze_window(self, window: list[dict]) -> str | None:
        """Analyze a 30-frame window for complex patterns like fatigue or speed drops."""
        if len(window) < 30:
            return None

        # 1. Check for speed drop in final phase (frames 20-30)
        hand_speeds = [f.get("hand_speed", 0.0) for f in window]
        first_half_avg = np.mean(hand_speeds[5:15])
        second_half_avg = np.mean(hand_speeds[20:30])
        
        if first_half_avg > 2.0 and second_half_avg < first_half_avg * 0.5:
            return "Tu velocidad cae después del frame 20. ¡Mantén la explosividad hasta el final!"

        # 2. Check for retraction speed (frames 15-30)
        retraction_speeds = [f.get("retraction_speed", 0.0) for f in window]
        max_retraction = np.max(retraction_speeds)
        if max_retraction < 0.5:
            return "No retraes el brazo rápido. Regresa la guardia inmediatamente."

        # 3. Check for torso rotation
        rotations = [f.get("torso_rotation", 0.0) for f in window]
        max_rot = np.max(rotations)
        if self.baseline_stats:
            baseline_rot = self.baseline_stats["mean"].get("torso_rotation", 0.1)
            if max_rot < baseline_rot * 0.6:
                return "Tu cadera no rota lo suficiente. Usa el núcleo para potenciar el golpe."

        return None

    def compare_realtime(self, user_features: dict) -> str | None:
        """Simple heuristic feedback for single frames."""
        if not user_features:
            return None

        # Low visibility check
        if user_features.get("tracking_state") == "searching":
            return "UBICA TU CUERPO EN EL CUADRO"

        elbow_angle = user_features.get("elbow_angle_left", 0.0)
        if elbow_angle < 100 and user_features.get("forward_extent_left", 0.0) > 0.2:
             return "Extiende completamente el brazo."

        return None
