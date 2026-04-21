"""Dataset builder for Random Forest classifier training.

Reads from build_baseline/dataset/baseline_final.parquet
and builds X, y training arrays using time-series features.
"""

from __future__ import annotations

import logging
from pathlib import Path

import numpy as np
import pandas as pd

from ml_service.dtw_scorer import DTW_FEATURE_ORDER

logger = logging.getLogger(__name__)


def extract_window_features(window_df: pd.DataFrame) -> np.ndarray:
    """Condense a 30-frame window into a flat feature vector for RF.
    
    Extracts min, max, mean, and std for each biomechanical feature.
    """
    stats = []
    for col in DTW_FEATURE_ORDER:
        if col not in window_df.columns:
            # Fallback for missing features
            stats.extend([0.0, 0.0, 0.0, 0.0])
            continue
            
        series = window_df[col].values
        stats.extend([
            float(np.min(series)),
            float(np.max(series)),
            float(np.mean(series)),
            float(np.std(series)),
        ])
    return np.array(stats)


def build_dataset(parquet_path: Path) -> tuple[np.ndarray, np.ndarray]:
    """Read parquet file and build (X, y) datasets.
    
    Since the parquet contains continuous frames from different punches,
    we group them by the 'punch_type' and 'synthetic' (or sequence id) 
    columns to form 30-frame windows.
    """
    logger.info("Loading dataset from %s", parquet_path)
    df = pd.read_parquet(parquet_path)
    
    if "punch_type" not in df.columns:
        raise ValueError("Dataset must contain 'punch_type' column for classification.")
        
    # We assume the parquet is already sorted by time/frame and chunks are 
    # roughly 30 frames. To simply extract instances, we can window by punch_type.
    # In a real scenario, there should be a 'sequence_id' to group by.
    # If not present, we will segment blindly by 30 frames where punch_type matches.
    group_col = "sequence_id" if "sequence_id" in df.columns else "punch_type"
    
    X_list = []
    y_list = []
    
    for name, group in df.groupby(group_col):
        # Name could be just 'jab' if grouped by punch_type, 
        # so we chunk it into 30 frame windows
        n_frames = len(group)
        ptype = group["punch_type"].iloc[0]
        
        for i in range(0, n_frames - 30 + 1, 15): # overlap by 15 frames
            window = group.iloc[i : i + 30]
            if len(window) == 30:
                features = extract_window_features(window)
                X_list.append(features)
                y_list.append(ptype)
                
    X = np.array(X_list)
    y = np.array(y_list)
    logger.info("Generated %d samples for training.", len(X))
    return X, y
