import sys
import types
sys.modules['cv2'] = types.ModuleType('cv2')
sys.modules['mediapipe'] = types.ModuleType('mediapipe')
import pandas as pd
import numpy as np

from ml_service.dtw_scorer import score_window, get_qualitative_label

def main():
    base_dir = r"c:\Users\Federico\Documents\projects\boxing-api\apps\backend\app"
    orig_path = base_dir + r"\baseline.parquet"
    aug_path = base_dir + r"\baseline_augmented_v2.parquet"
    
    orig_df = pd.read_parquet(orig_path)
    aug_df = pd.read_parquet(aug_path)
    
    orig_window = orig_df.head(30).to_dict('records')
    
    print("\n--- ORIGINAL vs ORIGINAL ---")
    sc = score_window(orig_window, orig_window)
    print(f"Score: {sc:.2f} | {get_qualitative_label(sc)}")
    
    print("\n--- ORIGINAL vs SYNTHETIC ---")
    scores = []
    # Test first 10 synthetic augmentations
    for aug_id in range(1, 11):
        syn_seq = aug_df[aug_df['aug_id'] == aug_id].head(30).to_dict('records')
        if len(syn_seq) < 30:
            continue
        sc = score_window(syn_seq, orig_window)
        scores.append(sc)
        print(f"Synthetic {aug_id} | Score: {sc:.2f} | {get_qualitative_label(sc)}")
        
    print(f"Avg Synthetic Score: {np.mean(scores):.2f}")
    
    print("\n--- ORIGINAL vs RANDOM ---")
    rand_scores = []
    for _ in range(5):
        rand_win = []
        for _ in range(30):
            rand_win.append({
                'elbow_angle_left': np.random.uniform(0, 180),
                'forward_extent_left': np.random.uniform(-0.5, 0.5),
                'hand_speed': np.random.uniform(0, 15),
                'retraction_speed': np.random.uniform(0, 5)
            })
        sc = score_window(rand_win, orig_window)
        rand_scores.append(sc)
        print(f"Random | Score: {sc:.2f} | {get_qualitative_label(sc)}")

if __name__ == "__main__":
    main()
