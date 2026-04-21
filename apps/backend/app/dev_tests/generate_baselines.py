#!/usr/bin/env python3
"""
Baseline Generator - Professional Video Processing Pipeline

Processes professional boxing videos to generate multiple baselines per punch type.
Creates both .parquet (runtime) and .json (debug) formats.

Usage:
    python generate_baselines.py

Input:
    build_baseline/videos/ (professional videos by punch type)

Output:
    dataset/
        jab/
            jab_v1.parquet
            jab_v1.json
            jab_v2.parquet
            jab_v2.json
            ...
        cross/
        hook/
        uppercut/
"""

import json
import logging
import random
import shutil
from pathlib import Path

import numpy as np
import pandas as pd

from build_baseline.build_pipeline import (
    build_punch, 
    FEATURE_ORDER, 
    filter_low_visibility, 
    smooth_series, 
    normalize, 
    augment
)
from ml_service.dtw_scorer import FEATURE_ORDER as DTW_FEATURE_ORDER

logger = logging.getLogger(__name__)

def select_random_videos(videos_dir: Path, punch_type: str, count: int = 3) -> list[Path]:
    """Select random videos from punch type directory."""
    videos = list(videos_dir.glob("*.mp4")) + list(videos_dir.glob("*.MOV"))
    if len(videos) <= count:
        return videos
    
    return random.sample(videos, count)

def process_video_to_features(video_path: Path) -> pd.DataFrame:
    """Process single video to extract features using MediaPipe pipeline."""
    # Import here to avoid circular imports
    from ml_service.boxing_jab_tracker import BoxingJabTracker
    
    import cv2
    
    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        logger.error(f"Cannot open video: {video_path}")
        return pd.DataFrame()
    
    tracker = BoxingJabTracker(baseline=None)
    fps = cap.get(cv2.CAP_PROP_FPS) or tracker.DEFAULT_FPS
    tracker.set_fps(fps)
    tracker.reset_state()
    
    features_list = []
    frame_count = 0
    
    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            
            _, features, _, _, _ = tracker.process_frame(frame)
            if features:
                features['frame_index'] = frame_count
                features_list.append(features)
                frame_count += 1
    
    finally:
        cap.release()
    
    if not features_list:
        logger.warning(f"No features extracted from {video_path}")
        return pd.DataFrame()
    
    df = pd.DataFrame(features_list)
    
    # Apply same processing as build_pipeline
    df = filter_low_visibility(df)
    df = smooth_series(df)
    df = normalize(df)
    
    return df

def create_baseline_dataframe(processed_dfs: list[pd.DataFrame], punch_type: str) -> pd.DataFrame:
    """Create final baseline from multiple processed videos."""
    if not processed_dfs:
        return pd.DataFrame()
    
    # Combine all processed data
    combined = pd.concat(processed_dfs, ignore_index=True)
    
    # Add metadata
    combined['punch_type'] = punch_type
    combined['baseline_version'] = f"{punch_type}_baseline"
    combined['source'] = 'professional_videos'
    
    return combined

def save_baseline_formats(df: pd.DataFrame, output_dir: Path, punch_type: str, version: int):
    """Save baseline in both .parquet and .json formats."""
    
    # Create output directory
    output_dir.mkdir(parents=True, exist_ok=True)
    
    base_name = f"{punch_type}_v{version}"
    
    # Save .parquet (runtime format)
    parquet_path = output_dir / f"{base_name}.parquet"
    df.to_parquet(parquet_path, index=False)
    logger.info(f"✅ Saved parquet: {parquet_path}")
    
    # Save .json (debug format)
    json_path = output_dir / f"{base_name}.json"
    
    # Create JSON structure with metadata
    baseline_data = {
        'metadata': {
            'punch_type': punch_type,
            'version': version,
            'total_frames': len(df),
            'features': list(df.columns),
            'created_at': pd.Timestamp.now().isoformat()
        },
        'features_avg': df.mean().to_dict(),
        'temporal_sequence': df[DTW_FEATURE_ORDER].fillna(0).values.tolist() if all(col in df.columns for col in DTW_FEATURE_ORDER) else [],
        'full_data': df.to_dict('records')[:50]  # First 50 frames for inspection
    }
    
    with open(json_path, 'w') as f:
        json.dump(baseline_data, f, indent=2, default=str)
    logger.info(f"✅ Saved JSON: {json_path}")
    
    return parquet_path, json_path

def generate_baselines_for_type(videos_dir: Path, dataset_dir: Path, punch_type: str, num_baselines: int = 3):
    """Generate multiple baselines for a specific punch type."""
    
    logger.info(f"🥊 Processing {punch_type} baselines...")
    
    # Select random videos
    selected_videos = select_random_videos(videos_dir / punch_type, punch_type, num_baselines)
    
    if not selected_videos:
        logger.warning(f"No videos found for {punch_type}")
        return []
    
    processed_dfs = []
    
    # Process each selected video
    for i, video_path in enumerate(selected_videos):
        logger.info(f"Processing video {i+1}/{len(selected_videos)}: {video_path.name}")
        
        # Process video to features
        features_df = process_video_to_features(video_path)
        
        if not features_df.empty:
            processed_dfs.append(features_df)
    
    if not processed_dfs:
        logger.error(f"No valid features extracted for {punch_type}")
        return []
    
    # Create baseline from combined data
    baseline_df = create_baseline_dataframe(processed_dfs, punch_type)
    
    # Save in multiple formats
    baseline_files = []
    for version in range(1, len(processed_dfs) + 1):
        # Use subset for each version
        subset_df = baseline_df.head(30 * version)  # Different windows for variety
        parquet_path, json_path = save_baseline_formats(
            subset_df, 
            dataset_dir / punch_type, 
            punch_type, 
            version
        )
        baseline_files.append((parquet_path, json_path))
    
    return baseline_files

def main():
    """Main baseline generation pipeline."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    base_dir = Path(__file__).parent
    videos_dir = base_dir / "build_baseline" / "videos"
    dataset_dir = base_dir / "dataset"
    
    punch_types = ["jab", "cross", "hook", "uppercut"]
    all_baseline_files = []
    
    logger.info("🚀 Starting baseline generation...")
    
    for punch_type in punch_types:
        baseline_files = generate_baselines_for_type(
            videos_dir, dataset_dir, punch_type, num_baselines=3
        )
        all_baseline_files.extend(baseline_files)
    
    # Generate summary
    summary = {
        'total_baselines': len(all_baseline_files),
        'punch_types': punch_types,
        'output_directory': str(dataset_dir),
        'files_created': [
            {
                'punch_type': f.parent.name,
                'version': f.stem.split('_v')[1],
                'parquet': str(parquet),
                'json': str(json)
            }
            for parquet, json in all_baseline_files
            for f in [parquet, json]
        ]
    }
    
    # Save summary
    summary_path = dataset_dir / "generation_summary.json"
    with open(summary_path, 'w') as f:
        json.dump(summary, f, indent=2, default=str)
    
    logger.info(f"🎯 Baseline generation complete!")
    logger.info(f"📊 Total baselines: {len(all_baseline_files) // 2}")
    logger.info(f"📁 Output directory: {dataset_dir}")
    logger.info(f"📋 Summary saved to: {summary_path}")

if __name__ == "__main__":
    main()
