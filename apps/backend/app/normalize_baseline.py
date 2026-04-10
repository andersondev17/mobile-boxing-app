import pandas as pd
import numpy as np
import os

def augment_sequence(df, noise_sigma=0.01, temporal_scale_range=(0.9, 1.1), amplitude_scale_range=(0.9, 1.1)):
    """
    Generate augmented sequences
    - slight gaussian noise
    - small temporal scaling (resampling)
    - minor amplitude scaling
    """
    augmented_dfs = []
    
    # Just single iteration or multiple? Let's just generate 3 augmented variations per original
    for i in range(3):
        aug_df = df.copy()
        
        # 1. Amplitude scaling
        amp_scale = np.random.uniform(*amplitude_scale_range)
        numeric_cols = ['elbow_angle', 'forward_extent', 'hand_speed', 'retraction_speed']
        for col in numeric_cols:
            if col in aug_df.columns:
                aug_df[col] = aug_df[col] * amp_scale
                
        # 2. Gaussian noise
        for col in numeric_cols:
            if col in aug_df.columns:
                noise = np.random.normal(0, noise_sigma, len(aug_df))
                aug_df[col] = aug_df[col] + noise
                
        # 3. Temporal scaling using linear interpolation
        temp_scale = np.random.uniform(*temporal_scale_range)
        orig_indices = np.arange(len(aug_df))
        new_length = int(len(aug_df) * temp_scale)
        if new_length > 1:
            new_indices = np.linspace(0, len(aug_df) - 1, new_length)
            
            temp_dict = {}
            for col in aug_df.columns:
                if col in numeric_cols:
                    temp_dict[col] = np.interp(new_indices, orig_indices, aug_df[col].values)
                else:
                    # For non-numeric like punch_type, we can just use nearest neighbor
                    temp_dict[col] = aug_df[col].values[np.round(new_indices).astype(int)]
            
            aug_df = pd.DataFrame(temp_dict)
            
        aug_df['augmentation_id'] = i
        augmented_dfs.append(aug_df)
        
    return pd.concat(augmented_dfs, ignore_index=True)

def main():
    base_dir = r"c:\Users\Federico\Documents\projects\boxing-api\apps\backend\app"
    baseline_path = os.path.join(base_dir, "baseline.parquet")
    
    print(f"Loading {baseline_path}")
    df = pd.read_parquet(baseline_path)
    
    print("Original stats:")
    print(df.describe())
    
    # 2. Normalize features
    df_norm = df.copy()
    if 'elbow_angle' in df_norm.columns:
        df_norm['elbow_angle'] = df_norm['elbow_angle'] / 180.0
    
    if 'hand_speed' in df_norm.columns:
        df_norm['hand_speed'] = df_norm['hand_speed'] / 15.0  # safe constant
        
    if 'retraction_speed' in df_norm.columns:
        df_norm['retraction_speed'] = df_norm['retraction_speed'] / 1.5 # scale to ~[0,1]
    
    # Validate distributions
    print("\nNormalized stats (Min/Max):")
    for col in ['elbow_angle', 'forward_extent', 'hand_speed', 'retraction_speed']:
        if col in df_norm.columns:
            print(f"{col}: Min = {df_norm[col].min():.4f}, Max = {df_norm[col].max():.4f}")
            
    # Save normalized
    norm_path = os.path.join(base_dir, "baseline_normalized.parquet")
    df_norm.to_parquet(norm_path)
    print(f"Saved {norm_path}")
    
    # 4. Generate simple augmentations
    print("Generating augmentations...")
    # we need to group by sequences but since this is presumably a single trajectory or bunch of punches...
    if 'punch_id' in df_norm.columns or 'sequence_id' in df_norm.columns:
        group_col = 'punch_id' if 'punch_id' in df_norm.columns else 'sequence_id'
        augmented = df_norm.groupby(group_col).apply(augment_sequence).reset_index(drop=True)
    else:
        # Assuming whole df is one sequence
        augmented = augment_sequence(df_norm)
        
    # 5. Save augmented
    aug_path = os.path.join(base_dir, "baseline_augmented.parquet")
    augmented.to_parquet(aug_path)
    print(f"Saved {aug_path}")

if __name__ == "__main__":
    main()
