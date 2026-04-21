import pandas as pd
import numpy as np
import random
import os
import sys
import types
from scipy.interpolate import interp1d

# Mocking modules for standalone execution
sys.modules['cv2'] = types.ModuleType('cv2')
sys.modules['mediapipe'] = types.ModuleType('mediapipe')

from ml_service.dtw_scorer import DTW_FEATURE_ORDER

def apply_temporal_noise(size, scale, correlation=0.8):
    noise = np.zeros(size)
    noise[0] = np.random.normal(0, scale)
    for i in range(1, size):
        noise[i] = correlation * noise[i-1] + np.sqrt(1 - correlation**2) * np.random.normal(0, scale)
    return noise

def generate_synthetic_data(df, augmentations_per_type=10):
    n_frames = len(df)
    frames_list = [df.head(30).to_dict('records')] if n_frames >= 30 else [df.to_dict('records')]
    
    augmented_records = []
    
    for seq in frames_list:
        seq_df = pd.DataFrame(seq)
        if len(seq_df) < 2: continue
            
        # 1. Add Original
        augmented_records.extend(seq_df.assign(synthetic=False, category='ORIGINAL', aug_id=0).to_dict('records'))
        
        aug_counter = 1
        for category in ['GOOD', 'ACCEPTABLE', 'BAD']:
            for _ in range(augmentations_per_type):
                # A. Temporal scaling
                orig_len = len(seq_df)
                if category == 'GOOD': target_len = random.randint(28, 32)
                elif category == 'ACCEPTABLE': target_len = random.randint(25, 40)
                else: target_len = random.randint(20, 50)
                    
                x_orig = np.linspace(0, 1, orig_len)
                x_target = np.linspace(0, 1, target_len)
                x_30 = np.linspace(0, 1, 30)
                
                temp_dict = {}
                for col in DTW_FEATURE_ORDER:
                    if col in seq_df.columns:
                        f_interp = interp1d(x_orig, seq_df[col].values, kind='linear', fill_value="extrapolate")
                        stretched = f_interp(x_target)
                        f_back = interp1d(np.linspace(0, 1, len(stretched)), stretched, kind='linear', fill_value="extrapolate")
                        temp_dict[col] = f_back(x_30)
                    else:
                        temp_dict[col] = np.zeros(30)
                
                aug_df = pd.DataFrame(temp_dict)
                
                # B. Amplitude & Noise & Fatigue
                fatigue_curve = np.ones(30)
                if category == 'BAD' and random.random() < 0.7:
                    # frames 0-10: 1.0, 10-20: 0.8, 20-30: 0.4
                    fatigue_curve = np.concatenate([np.ones(10), np.ones(10)*0.8, np.ones(10)*0.4])

                for col in DTW_FEATURE_ORDER:
                    scale_mult = 1.0
                    noise_scale = 0.01
                    
                    if category == 'GOOD':
                        scale_mult = random.uniform(0.98, 1.02)
                        noise_scale = 0.005
                    elif category == 'ACCEPTABLE':
                        scale_mult = random.uniform(0.90, 1.10)
                        noise_scale = 0.02
                    else: # BAD
                        scale_mult = random.uniform(0.1, 2.5)
                        noise_scale = 0.1
                        if col == 'torso_rotation': scale_mult = random.uniform(0, 0.2) # Static torso
                    
                    aug_df[col] = (aug_df[col] * scale_mult * fatigue_curve) + apply_temporal_noise(30, scale=noise_scale)

                aug_df = aug_df.assign(synthetic=True, category=category, aug_id=aug_counter, frame_index=np.arange(30))
                augmented_records.extend(aug_df.to_dict('records'))
                aug_counter += 1
            
    return pd.DataFrame(augmented_records)

def main():
    root_dir = r"c:\Users\Federico\Documents\projects\boxing-api"
    source_path = os.path.join(root_dir, "build_baseline", "baseline_final.parquet")
    output_path = os.path.join(root_dir, "dataset", "synthetic_dataset.parquet")
    
    if not os.path.exists(source_path):
        print(f"Error: {source_path} not found.")
        return

    df = pd.read_parquet(source_path)
    aug_df = generate_synthetic_data(df, augmentations_per_type=50)
    aug_df.to_parquet(output_path, index=False)
    print(f"Saved {len(aug_df)} synthetic samples to {output_path}")

if __name__ == "__main__":
    main()
