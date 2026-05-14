import sys
import types
sys.modules['cv2'] = types.ModuleType('cv2')
sys.modules['mediapipe'] = types.ModuleType('mediapipe')
import pandas as pd
import numpy as np

from services.ml.core.dtw_scorer import score_window, get_qualitative_label

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
    categories = ['GOOD', 'ACCEPTABLE', 'BAD']
    
    for cat in categories:
        cat_scores = []
        cat_df = aug_df[aug_df['category'] == cat]
        for aug_id in cat_df['aug_id'].unique():
            syn_seq = cat_df[cat_df['aug_id'] == aug_id].head(30).to_dict('records')
            if len(syn_seq) < 30:
                continue
            sc = score_window(syn_seq, orig_window)
            cat_scores.append(sc)
            
        print(f"--- Category: {cat} ---")
        if cat_scores:
            print(f"Mean: {np.mean(cat_scores):.2f}")
            print(f"Min:  {np.min(cat_scores):.2f}")
            print(f"Max:  {np.max(cat_scores):.2f}")
        else:
            print("No data.")

if __name__ == "__main__":
    main()






