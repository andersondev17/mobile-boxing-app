import pandas as pd
import numpy as np
import random
import os
import sys
import types
sys.modules['cv2'] = types.ModuleType('cv2')
sys.modules['mediapipe'] = types.ModuleType('mediapipe')
from scipy.interpolate import interp1d

from ml_service.dtw_scorer import DTW_FEATURE_ORDER

def generate_synthetic_data(df, augmentations=5):
    """
    Generate synthetic boxing trajectories from a baseline dataframe.
    """
    # Assuming df represents 30 frames or has a frame_index
    # Group by sequence or just treat the whole file as one sequence
    # For now, baseline.parquet contains a series of frames. 
    # Let's chunk them into 30 frame sequences if multiple, or just take first 30
    
    n_frames = len(df)
    if n_frames < 30:
        frames_list = [df.to_dict('records')]
    else:
        # Just use first 30 frames as base reference
        frames_list = [df.head(30).to_dict('records')]
        
    augmented_records = []
    
    for seq in frames_list:
        seq_df = pd.DataFrame(seq)
        if len(seq_df) < 2:
            augmented_records.extend(seq)
            continue
            
        # Add original
        seq_df['synthetic'] = False
        seq_df['aug_id'] = 0
        augmented_records.extend(seq_df.to_dict('records'))
        
        for aug_idx in range(1, augmentations + 1):
            aug_df = seq_df.copy()
            
            # A. Temporal scaling (resample and interpolate back to 30)
            orig_len = len(aug_df)
            target_len = random.randint(25, 40)
            
            x_orig = np.linspace(0, 1, orig_len)
            x_target = np.linspace(0, 1, target_len)
            x_30 = np.linspace(0, 1, 30)
            
            temp_dict = {}
            for col in DTW_FEATURE_ORDER:
                if col in aug_df.columns:
                    # 1. stretch/compress
                    f_interp = interp1d(x_orig, aug_df[col].values, kind='linear', fill_value="extrapolate")
                    stretched = f_interp(x_target)
                    
                    # 2. interpolate back to 30 for tensor strictness
                    f_back = interp1d(np.linspace(0, 1, len(stretched)), stretched, kind='linear', fill_value="extrapolate")
                    final_30 = f_back(x_30)
                    temp_dict[col] = final_30
                else:
                    temp_dict[col] = np.zeros(30)
            
            # Reconstruct to 30 frames
            aug_df = pd.DataFrame(temp_dict)
            
            # B. Amplitude scaling & C. Gaussian noise
            for col in DTW_FEATURE_ORDER:
                if col == "elbow_angle_left":
                    amp = random.uniform(0.95, 1.05)
                    noise = np.random.normal(0, 2.0, 30) # 2 degrees noise
                elif col == "forward_extent_left":
                    amp = random.uniform(0.9, 1.1)
                    noise = np.random.normal(0, 0.02, 30)
                elif "speed" in col:
                    amp = random.uniform(0.85, 1.15)
                    noise = np.random.normal(0, 0.5, 30)
                else:
                    amp = 1.0
                    noise = 0.0
                    
                aug_df[col] = aug_df[col] * amp + noise
                
            # D. Biomechanical perturbations (shift timing)
            # Roll hand speed slightly to simulate late retraction
            if 'hand_speed' in aug_df.columns and 'retraction_speed' in aug_df.columns:
                shift = random.choice([-2, -1, 1, 2])
                aug_df['retraction_speed'] = np.roll(aug_df['retraction_speed'].values, shift)
                # Keep bounds valid
                aug_df['retraction_speed'] = np.clip(aug_df['retraction_speed'], 0, None)
                aug_df['hand_speed'] = np.clip(aug_df['hand_speed'], 0, None)
                
            aug_df['synthetic'] = True
            aug_df['aug_id'] = aug_idx
            aug_df['frame_index'] = np.arange(30)
            
            augmented_records.extend(aug_df.to_dict('records'))
            
    return pd.DataFrame(augmented_records)

def main():
    base_dir = r"c:\Users\Federico\Documents\projects\boxing-api\apps\backend\app"
    source_path = os.path.join(base_dir, "baseline.parquet")
    output_path = os.path.join(base_dir, "baseline_augmented_v2.parquet")
    
    print(f"Loading {source_path}")
    df = pd.read_parquet(source_path)
    
    aug_df = generate_synthetic_data(df, augmentations=20)
    
    # Validate strictly follows DTW_FEATURE_ORDER
    print("Columns:", [c for c in aug_df.columns if c in DTW_FEATURE_ORDER])
    
    # Save unnormalized (normalization happens at runtime)
    aug_df.to_parquet(output_path, index=False)
    print(f"Saved synthetic enriched dataset to: {output_path}")

if __name__ == "__main__":
    main()
