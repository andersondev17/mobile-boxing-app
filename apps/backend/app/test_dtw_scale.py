import sys
import types
sys.modules['cv2'] = types.ModuleType('cv2')
sys.modules['mediapipe'] = types.ModuleType('mediapipe')
import pandas as pd
import numpy as np
import random
from ml_service.dtw_scorer import score_window, get_qualitative_label, _window_to_matrix, DTW_K
from dtaidistance import dtw_ndim
import math

def generate_experiments():
    base_dir = r"c:\Users\Federico\Documents\projects\boxing-api\apps\backend\app"
    baseline_path = base_dir + r"\baseline.parquet"
    df = pd.read_parquet(baseline_path)
    
    # ensure it has the same columns expected
    baseline_window = df.head(30).to_dict('records')
    
    print(f"--- EXPERIMENT DTW_K = {DTW_K} ---")
    
    # 1. Identical window
    sc = score_window(baseline_window, baseline_window)
    print(f"[Identical] Score: {sc:.2f} | Label: {get_qualitative_label(sc)}")
    
    # 2. Perturbed windows (20 runs)
    print("\n--- Perturbed Windows ---")
    scores = []
    distances = []
    
    base_mat = _window_to_matrix(baseline_window)
    
    for i in range(20):
        # Slightly perturbed frame features
        perturbed = []
        for frame in baseline_window:
            p_frame = frame.copy()
            noise = random.uniform(0.9, 1.1)
            for k in ['elbow_angle_left', 'forward_extent_left', 'hand_speed', 'retraction_speed']:
                p_frame[k] = p_frame[k] * noise + random.uniform(-0.05, 0.05) if k in p_frame else 0.0
            perturbed.append(p_frame)
            
        p_mat = _window_to_matrix(perturbed)
        distance = dtw_ndim.distance(p_mat, base_mat)
        sc = score_window(perturbed, baseline_window)
        scores.append(sc)
        distances.append(distance)
        print(f"Run {i+1} | Dist: {distance:.4f} | Score: {sc:.2f} | Label: {get_qualitative_label(sc)}")
        
    # 3. Random window
    print("\n--- Random Window ---")
    rand_win = []
    for _ in range(30):
        r_frame = {
            'elbow_angle_left': random.uniform(0, 180),
            'forward_extent_left': random.uniform(-0.5, 0.5),
            'hand_speed': random.uniform(0, 25),
            'retraction_speed': random.uniform(0, 5)
        }
        rand_win.append(r_frame)
    sc = score_window(rand_win, baseline_window)
    print(f"[Random] Score: {sc:.2f} | Label: {get_qualitative_label(sc)}")

if __name__ == "__main__":
    generate_experiments()
