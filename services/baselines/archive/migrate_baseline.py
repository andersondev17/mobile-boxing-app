import pandas as pd
import os
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def migrate():
    base_dir = r"c:\Users\Federico\Documents\projects\boxing-api\apps\backend\app"
    baseline_path = os.path.join(base_dir, "baseline.parquet")
    
    if not os.path.exists(baseline_path):
        logger.error(f"{baseline_path} not found.")
        return
        
    df = pd.read_parquet(baseline_path)
    
    rename_map = {}
    if 'elbow_angle' in df.columns:
        rename_map['elbow_angle'] = 'elbow_angle_left'
    if 'forward_extent' in df.columns:
        rename_map['forward_extent'] = 'forward_extent_left'
        
    if rename_map:
        df = df.rename(columns=rename_map)
        logger.info(f"Renamed columns: {rename_map}")
        
    required_cols = ['elbow_angle_left', 'forward_extent_left', 'hand_speed', 'retraction_speed']
    for col in required_cols:
        if col not in df.columns:
            logger.warning(f"Column {col} is missing, filling with 0.0")
            df[col] = 0.0
            
    df.to_parquet(baseline_path, index=False)
    logger.info(f"Migrated {baseline_path} successfully.")

if __name__ == "__main__":
    migrate()






