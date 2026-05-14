"""
Baseline Builder — Full Multi-Punch Pipeline

Pipeline:
  1. Iterates over punch directories in build_baseline/videos/
  2. Processes video -> landmarks -> features -> filter -> smooth -> normalize -> augment
  3. Saves intermediate per-punch parquets in build_baseline/processed_videos/
  4. Concatenates all into a single dataset/baseline_final.parquet
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.interpolate import interp1d

from services.ml.core.dtw_scorer import DTW_FEATURE_ORDER
from services.ml.core.frame_quality import validate_frame, smooth_features

logger = logging.getLogger(__name__)

NORM = {
    "elbow_angle_left": 180.0,
    "knee_flexion": 180.0,
    "hand_speed": 15.0,
    "retraction_speed": 5.0,
    "torso_rotation": 0.5,
    "hip_rotation": 0.5,
}

def filter_low_visibility(df: pd.DataFrame) -> pd.DataFrame:
    required = ["elbow_angle_left", "forward_extent_left"]
    mask = (df[required] != 0.0).all(axis=1)
    return df[mask].reset_index(drop=True)

def smooth_series(df: pd.DataFrame, alpha: float = 0.7) -> pd.DataFrame:
    out = df.copy()
    for col in DTW_FEATURE_ORDER:
        if col in out.columns:
            out[col] = out[col].ewm(alpha=alpha, adjust=False).mean()
    return out

def normalize(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    for col, denom in NORM.items():
        if col in out.columns and denom != 0:
            out[col] = out[col] / denom
    if "vertical_displacement" in out.columns:
        out["vertical_displacement"] = (out["vertical_displacement"] + 0.2) / 0.5
    for col in ("forward_extent_left", "weight_transfer"):
        if col in out.columns:
            out[col] = out[col] + 0.5
    return out

def _temporal_noise(size: int, scale: float, corr: float = 0.8) -> np.ndarray:
    noise = np.zeros(size)
    noise[0] = np.random.normal(0, scale)
    for i in range(1, size):
        noise[i] = corr * noise[i - 1] + np.sqrt(1 - corr ** 2) * np.random.normal(0, scale)
    return noise

def augment(df: pd.DataFrame, punch_type: str, n_good: int = 5, n_acceptable: int = 5) -> pd.DataFrame:
    records = df.to_dict("records")
    augmented = []
    
    # original frames get punch_type
    for r in records:
        r["punch_type"] = punch_type
        r["synthetic"] = False
        r["sequence_id"] = f"{punch_type}_orig_1"
        augmented.append(r)

    window = df.head(30)
    if len(window) < 2:
        return pd.DataFrame(augmented)

    x_orig = np.linspace(0, 1, len(window))
    x_30 = np.linspace(0, 1, 30)

    def _resample(target_len: int) -> pd.DataFrame:
        x_t = np.linspace(0, 1, target_len)
        tmp = {}
        for col in DTW_FEATURE_ORDER:
            if col not in window.columns:
                tmp[col] = np.zeros(30)
                continue
            f = interp1d(x_orig, window[col].values[:len(x_orig)], kind="linear", fill_value="extrapolate")
            stretched = f(x_t)
            f2 = interp1d(np.linspace(0, 1, len(stretched)), stretched, kind="linear", fill_value="extrapolate")
            tmp[col] = f2(x_30)
        return pd.DataFrame(tmp)

    for i in range(n_good):
        aug = _resample(np.random.randint(28, 32))
        for col in DTW_FEATURE_ORDER:
            aug[col] = aug[col] * np.random.uniform(0.98, 1.02) + _temporal_noise(30, 0.005)
        aug["category"] = "GOOD"
        aug["synthetic"] = True
        aug["punch_type"] = punch_type
        aug["sequence_id"] = f"{punch_type}_good_{i}"
        augmented.extend(aug.to_dict("records"))

    for i in range(n_acceptable):
        aug = _resample(np.random.randint(25, 40))
        for col in DTW_FEATURE_ORDER:
            aug[col] = aug[col] * np.random.uniform(0.90, 1.10) + _temporal_noise(30, 0.02)
        aug["category"] = "ACCEPTABLE"
        aug["synthetic"] = True
        aug["punch_type"] = punch_type
        aug["sequence_id"] = f"{punch_type}_acc_{i}"
        augmented.extend(aug.to_dict("records"))

    return pd.DataFrame(augmented)

def build_punch(raw_parquet: Path, output_parquet: Path, punch_type: str) -> pd.DataFrame:
    if not raw_parquet.exists():
        logger.warning("No raw parquet found at %s", raw_parquet)
        return pd.DataFrame()
        
    df = pd.read_parquet(raw_parquet)
    df = filter_low_visibility(df)
    df = smooth_series(df)
    df = normalize(df)
    df = augment(df, punch_type=punch_type)
    
    output_parquet.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(output_parquet, index=False)
    logger.info("✅ Saved intermediate: %s", output_parquet)
    return df

def merge_video_features(video_paths: list[Path]) -> pd.DataFrame:
    """Concatena features de múltiples videos del mismo tipo de golpe."""
    dfs = []
    for path in video_paths:
        df = extract_features_from_video(path)
        df['source_video'] = path.name
        dfs.append(df)
    return pd.concat(dfs, ignore_index=True)

def extract_features_from_video(video_path: Path) -> pd.DataFrame:
    """Extract features from a single video file."""
    # TODO: Implement video processing logic
    # This should call the existing video processing pipeline
    # For now, return empty DataFrame as placeholder
    return pd.DataFrame()

def process_punch_features(df: pd.DataFrame, punch_type: str, processed_dir: Path) -> pd.DataFrame:
    df = filter_low_visibility(df)
    df = smooth_series(df)
    df = normalize(df)
    df = augment(df, punch_type=punch_type)
    
    output_parquet = processed_dir / f"{punch_type}_processed.parquet"
    output_parquet.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(output_parquet, index=False)
    logger.info("✅ Saved intermediate: %s", output_parquet)
    return df

def build_all(videos_dir: Path, processed_dir: Path, final_out: Path) -> None:
    punches = ["jab", "cross", "gancho", "uppercut"]
    all_dfs = []
    
    for punch in punches:
        # Check for multiple videos in the punch directory
        punch_video_dir = videos_dir / punch
        if not punch_video_dir.exists():
            logger.warning(f" No video directory found for {punch} at {punch_video_dir}")
            continue
            
        # Find all video files in the punch directory
        video_files = list(punch_video_dir.glob("*.mp4")) + list(punch_video_dir.glob("*.MOV"))
        
        if not video_files:
            logger.warning(f" No video files found for {punch} in {punch_video_dir}")
            continue
            
        logger.info(f" Found {len(video_files)} videos for {punch}: {[f.name for f in video_files]}")
        
        # Process multiple videos and merge features
        try:
            merged_df = merge_video_features(video_files)
            if merged_df.empty:
                logger.warning(f" No features extracted from {punch} videos")
                continue
                
            # Process the merged features
            processed_df = process_punch_features(merged_df, punch, processed_dir)
            all_dfs.append(processed_df)
            
        except Exception as exc:
            logger.exception(f" Error processing {punch} videos: {exc}")
            continue
            
    if not all_dfs:
        logger.error("No data processed.")
        sys.exit(1)
        
    final_df = pd.concat(all_dfs, ignore_index=True)
    final_out.parent.mkdir(parents=True, exist_ok=True)
    final_df.to_parquet(final_out, index=False)
    logger.info("🚀 FINAL BASELINE GENERATED: %s (%d rows)", final_out, len(final_df))

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    base = Path(__file__).parent
    build_all(
        base / "videos",
        base / "processed_videos",
        base / "dataset" / "baseline_final.parquet"
    )






