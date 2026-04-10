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

def apply_temporal_noise(size, scale, correlation=0.8):
    """Generate temporally correlated noise (AR(1) process)."""
    noise = np.zeros(size)
    noise[0] = np.random.normal(0, scale)
    for i in range(1, size):
        noise[i] = correlation * noise[i-1] + np.sqrt(1 - correlation**2) * np.random.normal(0, scale)
    return noise

def generate_synthetic_data(df, augmentations_per_type=10):
    """
    Generate synthetic boxing trajectories from a baseline dataframe.
    """
    n_frames = len(df)
    if n_frames < 30:
        frames_list = [df.to_dict('records')]
    else:
        frames_list = [df.head(30).to_dict('records')]
        
    augmented_records = []
    
    for seq in frames_list:
        seq_df = pd.DataFrame(seq)
        if len(seq_df) < 2:
            augmented_records.extend(seq)
            continue
            
        # 1. Add Original
        seq_df['synthetic'] = False
        seq_df['category'] = 'ORIGINAL'
        seq_df['aug_id'] = 0
        augmented_records.extend(seq_df.to_dict('records'))
        
        # Generation loop
        aug_counter = 1
        for category in ['GOOD', 'ACCEPTABLE', 'BAD']:
            for _ in range(augmentations_per_type):
                aug_df = seq_df.copy()
                
                # A. Temporal scaling (resample and interpolate back to 30)
                orig_len = len(aug_df)
                
                if category == 'GOOD':
                    target_len = random.randint(28, 32)
                elif category == 'ACCEPTABLE':
                    target_len = random.randint(25, 40)
                else: # BAD
                    target_len = random.randint(20, 50) # Very fast or very slow
                    
                x_orig = np.linspace(0, 1, orig_len)
                x_target = np.linspace(0, 1, target_len)
                x_30 = np.linspace(0, 1, 30)
                
                temp_dict = {}
                for col in DTW_FEATURE_ORDER:
                    if col in aug_df.columns:
                        f_interp = interp1d(x_orig, aug_df[col].values, kind='linear', fill_value="extrapolate")
                        stretched = f_interp(x_target)
                        f_back = interp1d(np.linspace(0, 1, len(stretched)), stretched, kind='linear', fill_value="extrapolate")
                        final_30 = f_back(x_30)
                        temp_dict[col] = final_30
                    else:
                        temp_dict[col] = np.zeros(30)
                
                aug_df = pd.DataFrame(temp_dict)
                
                # B. Amplitude scaling & C. Realistic Noise
                for col in DTW_FEATURE_ORDER:
                    if category == 'GOOD':
                        amp = random.uniform(0.98, 1.02)
                        noise = apply_temporal_noise(30, scale=0.5 if 'angle' in col else 0.005)
                    elif category == 'ACCEPTABLE':
                        amp = random.uniform(0.90, 1.10)
                        noise = apply_temporal_noise(30, scale=2.0 if 'angle' in col else 0.02)
                    else: # BAD
                        amp = random.uniform(0.10, 3.00) # Terribly incorrect amplitude
                        noise = apply_temporal_noise(30, scale=30.0 if 'angle' in col else 1.5, correlation=0.1)
                        
                        # Add sensor jitter / dropped frame artifact severely
                        if random.random() < 0.9:
                            drop_idx = random.randint(5, 15)
                            noise[drop_idx:drop_idx+12] = noise[drop_idx-1] # Long Freeze frame artifact
                            
                    aug_df[col] = aug_df[col] * amp + noise
                    
                # D. Biomechanical perturbations
                if 'hand_speed' in aug_df.columns and 'retraction_speed' in aug_df.columns:
                    if category == 'ACCEPTABLE':
                        shift = random.choice([-2, -1, 1, 2])
                        aug_df['retraction_speed'] = np.roll(aug_df['retraction_speed'].values, shift)
                    elif category == 'BAD':
                        shift = random.choice([-20, -15, 15, 20]) # Complete disconnect between forward and retract
                        aug_df['retraction_speed'] = np.roll(aug_df['retraction_speed'].values, shift)
                        aug_df['forward_extent_left'] *= random.uniform(-0.5, 0.2) # Complete garbage extent
                        
                    aug_df['retraction_speed'] = np.clip(aug_df['retraction_speed'], 0, None)
                    aug_df['hand_speed'] = np.clip(aug_df['hand_speed'], 0, None)
                    
                aug_df['synthetic'] = True
                aug_df['category'] = category
                aug_df['aug_id'] = aug_counter
                aug_df['frame_index'] = np.arange(30)
                
                augmented_records.extend(aug_df.to_dict('records'))
                aug_counter += 1
            
    return pd.DataFrame(augmented_records)

def main():
    base_dir = r"c:\Users\Federico\Documents\projects\boxing-api\apps\backend\app"
    source_path = os.path.join(base_dir, "baseline.parquet")
    output_path = os.path.join(base_dir, "baseline_augmented_v2.parquet")
    
    print(f"Loading {source_path}")
    df = pd.read_parquet(source_path)
    
    aug_df = generate_synthetic_data(df, augmentations_per_type=20)
    
    # Validate strictly follows DTW_FEATURE_ORDER
    print("Columns:", [c for c in aug_df.columns if c in DTW_FEATURE_ORDER])
    
    # Save unnormalized
    aug_df.to_parquet(output_path, index=False)
    print(f"Saved synthetic enriched dataset to: {output_path}")

if __name__ == "__main__":
    main()
