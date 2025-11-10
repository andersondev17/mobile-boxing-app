import mediapipe as mp
import cv2
import numpy as np
from math import degrees, acos
import time

mp_pose = mp.solutions.pose
mp_drawing = mp.solutions.drawing_utils

class ContadorDominadas:
    """Clase para encapsular la lógica del contador de dominadas"""
    
    def __init__(self):
        self.up = False
        self.down = False
        self.count = 0
        self.state = "Esperando"
    
    def reset(self):
        """Reinicia el contador"""
        self.up = False
        self.down = False
        self.count = 0
        self.state = "Esperando"
    
    def actualizar_estado(self, mean_angle):
        """Actualiza el estado basado en el ángulo promedio"""
        if mean_angle > 150:
            self.up = True
            self.state = "Sube"
        elif self.up and not self.down and mean_angle < 55:
            self.down = True
            self.state = "Bien hecho"
        if self.up and self.down and mean_angle > 150:
            self.count += 1
            self.up = self.down = False
            self.state = "Reinicio"
        
        return self.count, self.state

def get_point(results, index, width, height):
    """Devuelve las coordenadas (x,y) de un landmark"""
    lm = results.pose_landmarks.landmark[index]
    return int(lm.x * width), int(lm.y * height)

def calculate_angle(p1, p2, p3):
    """Calcula el ángulo formado por 3 puntos"""
    l1 = np.linalg.norm(p2 - p3)
    l2 = np.linalg.norm(p1 - p3)
    l3 = np.linalg.norm(p1 - p2)
    cos_angle = (l1**2 + l3**2 - l2**2) / (2 * l1 * l3)
    cos_angle = np.clip(cos_angle, -1.0, 1.0)
    return degrees(acos(cos_angle))

def draw_zone(frame, p1, p2, p3, angle):
    """Dibuja las líneas y puntos de seguimiento"""
    color = (255, 255, 0)
    cv2.line(frame, tuple(p1), tuple(p2), color, 6)
    cv2.line(frame, tuple(p2), tuple(p3), color, 6)
    cv2.circle(frame, tuple(p1), 6, (0, 255, 255), 3)
    cv2.circle(frame, tuple(p2), 6, (128, 0, 250), 3)
    cv2.circle(frame, tuple(p3), 6, (255, 191, 0), 3)
    cv2.putText(frame, f"{int(angle)}°", tuple(p2 + np.array([20, -20])), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

def procesar_frame(frame, pose, contador):
    """
    Procesa un solo frame y retorna la información de seguimiento
    
    Args:
        frame: Frame de video (numpy array)
        pose: Instancia de MediaPipe Pose
        contador: Instancia de ContadorDominadas
    
    Returns:
        dict con count, state, landmarks, y el frame procesado
    """
    height, width, _ = frame.shape
    
    # Procesar con MediaPipe
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = pose.process(rgb)
    
    response_data = {
        "count": contador.count,
        "state": contador.state,
        "landmarks": None,
        "frame": frame
    }
    
    if results.pose_landmarks:
        # Obtener puntos
        right_shoulder = np.array(get_point(results, 12, width, height))
        right_elbow = np.array(get_point(results, 14, width, height))
        right_wrist = np.array(get_point(results, 16, width, height))
        left_shoulder = np.array(get_point(results, 11, width, height))
        left_elbow = np.array(get_point(results, 13, width, height))
        left_wrist = np.array(get_point(results, 15, width, height))
        
        # Calcular ángulos
        angle_r = calculate_angle(right_shoulder, right_elbow, right_wrist)
        angle_l = calculate_angle(left_shoulder, left_elbow, left_wrist)
        mean_angle = (angle_r + angle_l) / 2
        
        # Actualizar contador
        contador.actualizar_estado(mean_angle)
        
        # Visualización (opcional, para video)
        draw_zone(frame, right_shoulder, right_elbow, right_wrist, angle_r)
        draw_zone(frame, left_shoulder, left_elbow, left_wrist, angle_l)
        
        # Preparar datos de respuesta
        response_data["landmarks"] = {
            "right_shoulder": right_shoulder.tolist(),
            "right_elbow": right_elbow.tolist(),
            "right_wrist": right_wrist.tolist(),
            "left_shoulder": left_shoulder.tolist(),
            "left_elbow": left_elbow.tolist(),
            "left_wrist": left_wrist.tolist(),
            "angle_r": float(angle_r),
            "angle_l": float(angle_l)
        }
        response_data["count"] = contador.count
        response_data["state"] = contador.state
        response_data["frame"] = frame
    
    return response_data

def procesar_video(input_path, output_path):
    """Procesa un video completo y genera un video de salida"""
    cap = cv2.VideoCapture(input_path)
    
    if not cap.isOpened():
        raise ValueError(f"No se pudo abrir el video: {input_path}")
    
    # Obtener propiedades del video
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = int(cap.get(cv2.CAP_PROP_FPS))
    
    # Crear escritor de video con codec compatible con navegadores
    # Intentar H.264 primero (mejor compatibilidad)
    fourcc = cv2.VideoWriter_fourcc(*'avc1')  # H.264
    out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
    
    # Si falla, intentar con mp4v
    if not out.isOpened():
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
    
    # Inicializar contador y pose
    contador = ContadorDominadas()
    prev_time = time.time()
    
    with mp_pose.Pose(
        min_tracking_confidence=0.5,
        min_detection_confidence=0.5,
        static_image_mode=False
    ) as pose:
        while cap.isOpened():
            status, frame = cap.read()
            if not status:
                break
            
            # Procesar frame
            resultado = procesar_frame(frame, pose, contador)
            frame_procesado = resultado["frame"]
            
            # Agregar contador y estado al video
            cv2.rectangle(frame_procesado, (0, 0), (150, 80), (0, 0, 0), -1)
            cv2.putText(frame_procesado, str(resultado["count"]), (10, 60), 
                       cv2.FONT_HERSHEY_SIMPLEX, 2, (0, 0, 255), 3)
            cv2.putText(frame_procesado, resultado["state"], (100, 60), 
                       cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
            
            # FPS
            curr_time = time.time()
            fps_display = 1 / (curr_time - prev_time)
            prev_time = curr_time
            cv2.putText(frame_procesado, f"FPS: {int(fps_display)}", 
                       (width - 150, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
            
            # Escribir frame
            out.write(frame_procesado)
    
    cap.release()
    out.release()
    
    return {
        "total_pullups": contador.count,
        "output_path": output_path
    }

if __name__ == "__main__":
    # Modo desarrollo/prueba
    procesar_video("input.mp4", "output.mp4")