import numpy as np
import logging

logger = logging.getLogger(__name__)

class SpanishBoxingFeedback:
    """Spanish coaching feedback for boxing techniques."""
    
    COACHING_MESSAGES = {
        'jab': {
            'chin_up': "¡Levanta el mentón! Protege tu barbilla.",
            'arm_extension': "Extiende más el brazo. Alcanza más lejos con el jab.",
            'elbow_retraction': "Retrae el codo más rápido. Vuelve a la guardia inmediatamente.",
            'hip_rotation': "Gira la cadera. Usa el cuerpo completo para potenciar el golpe.",
            'balance': "Mejora tu equilibrio. Mantén el peso en las piernas.",
            'shoulder_guard': "Mantén el hombro de protección en la barbilla.",
            'speed_consistency': "Mantén la velocidad constante. No desaceleres al final."
        },
        'cross': {
            'chin_down': "¡Mentón abajo! Siempre protegido durante el cross.",
            'torso_rotation': "Gira más el torso. Potencia desde las caderas y hombros.",
            'full_extension': "Extiende completamente el brazo de cruzado.",
            'rear_hand_guard': "Mantén la mano trasera en la barbilla.",
            'weight_transfer': "Transfiere el peso. Usa las piernas para generar fuerza.",
            'follow_through': "Acompaña el golpe. Extiende completamente el brazo."
        },
        'hook': {
            'elbow_angle': "Mantén el codo en 90 grados. Brazo en forma de gancho.",
            'hip_explosion': "Explota la cadera. Genera potencia rotacional.",
            'short_range': "Gancho de corto alcance. Cerca y explosivo.",
            'body_rotation': "Gira el cuerpo completo. Involucra torso y caderas."
        },
        'uppercut': {
            'vertical_trajectory': "Trajectoria vertical. Golpe de abajo hacia arriba.",
            'knee_bend': "Dobilla flexionada. Genera fuerza desde las piernas.",
            'body_drop': "Baja el cuerpo. Usa gravedad para potenciar el golpe.",
            'chin_protection': "Barbilla protegida. Siempre hacia adentro."
        }
    }
    
    MOTIVATIONAL_MESSAGES = [
        "⚡ ¡Excelente potencia en ese golpe!",
        "🎯 Buena precisión y alcance.",
        "💪 Sigue así, tu técnica está mejorando.",
        "🔥 Gran explosividad en el movimiento!",
        "✨ Perfecta coordinación cuerpo-brazo.",
        "👊 Excelente forma técnica.",
        "🚀 Velocidad impresionante.",
        "💎 Calidad profesional en ese golpe.",
        "🌟 Sigue progresando así."
    ]
    
    def get_coaching_feedback(self, punch_type: str, features: dict) -> list:
        """Get specific coaching feedback based on punch type and features."""
        if punch_type not in self.COACHING_MESSAGES:
            return []
        
        messages = []
        coaching_set = self.COACHING_MESSAGES[punch_type]
        
        # Analyze specific features for each punch type
        if punch_type == 'jab':
            if features.get('forward_extent_left', 0) < 0.4:
                messages.append(coaching_set['arm_extension'])
            if features.get('hand_speed', 0) < 8.0:
                messages.append(coaching_set['speed_consistency'])
            if features.get('torso_rotation', 0) < 0.1:
                messages.append(coaching_set['hip_rotation'])
                
        elif punch_type == 'cross':
            if features.get('torso_rotation', 0) < 0.2:
                messages.append(coaching_set['torso_rotation'])
            if features.get('forward_extent_right', 0) < 0.6:
                messages.append(coaching_set['full_extension'])
            if features.get('weight_transfer', 0) < 0.7:
                messages.append(coaching_set['weight_transfer'])
                
        elif punch_type == 'hook':
            if features.get('elbow_angle_left', 180) > 120:
                messages.append(coaching_set['elbow_angle'])
            if features.get('hip_rotation', 0) < 0.15:
                messages.append(coaching_set['hip_explosion'])
                
        elif punch_type == 'uppercut':
            if features.get('vertical_displacement', 0) < 0.3:
                messages.append(coaching_set['vertical_trajectory'])
            if features.get('knee_flexion', 0) < 0.2:
                messages.append(coaching_set['knee_bend'])
        
        # Add general feedback
        if features.get('hand_speed', 0) > 12.0:
            messages.append(np.random.choice(self.MOTIVATIONAL_MESSAGES))
            
        return messages[:3]  # Limit to 3 messages max
    
    def get_motivational_message(self) -> str:
        """Get a random motivational message."""
        return np.random.choice(self.MOTIVATIONAL_MESSAGES)

class FeedbackEngine:
    """Intelligent coaching engine for real-time boxing technique feedback.
    
    Compares user feature windows against professional baselines to identify
    specific biomechanical errors (speed drops, lack of rotation, poor retraction).
    """

    def __init__(self, baseline_df=None):
        self.baseline_stats = None
        self.spanish_feedback = SpanishBoxingFeedback()
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
        """Enhanced heuristic feedback with motivational phrases."""
        if not user_features:
            return None

        # Low visibility check
        if user_features.get("tracking_state") == "searching":
            return "🎯 ¡Perfecto! Posición detectada. Ahora mantén la postura."

        elbow_angle = user_features.get("elbow_angle_left", 180.0)
        hand_speed = user_features.get("hand_speed", 0.0)
        forward_extent = user_features.get("forward_extent_left", 0.0)
        torso_rotation = user_features.get("torso_rotation", 0.0)
        
        # Technique-specific feedback with motivation
        if elbow_angle < 100 and forward_extent > 0.2:
             return "💪 ¡Excelente extensión! Sigue manteniendo esa potencia en el brazo."
        
        if hand_speed > 10.0:
            return "⚡ ¡Velocidad impresionante! Mantén esa explosividad en cada golpe."
        
        if forward_extent > 0.6:
            return "🎯 Gran alcance! Estás conectando bien con el objetivo."
        
        # Specific coaching feedback
        if elbow_angle > 160:
            return "👊 Postura perfecta! Tu técnica está mejorando notablemente."
            
        if torso_rotation < 0.1:
            return "🔄 Gira más el torso. Usa las caderas para generar potencia."
            
        if hand_speed < 5.0:
            return "🚀 Aumenta la velocidad del brazo. Sé más explosivo."
        
        # Add motivational message for good performance
        if hand_speed > 8.0 and torso_rotation > 0.15:
            return self.spanish_feedback.get_motivational_message()
        
        return None
