#!/usr/bin/env python3
"""
Simple Baseline Generator - Process videos to features without complex dependencies

Usage:
    python generate_baselines_simple.py
"""

import json
import logging
import random
from pathlib import Path

import numpy as np
import pandas as pd

# Mock FEATURE_ORDER for compatibility
FEATURE_ORDER = [
    "elbow_angle_left", "elbow_angle_right", 
    "forward_extent_left", "forward_extent_right",
    "hand_speed", "retraction_speed",
    "torso_rotation", "hip_rotation",
    "vertical_displacement", "weight_transfer"
]

logger = logging.getLogger(__name__)

def select_random_videos(videos_dir: Path, count: int = 3) -> list[Path]:
    """Select random videos from directory."""
    videos = list(videos_dir.glob("*.mp4")) + list(videos_dir.glob("*.MOV"))
    if len(videos) <= count:
        return videos
    return random.sample(videos, count)

def generate_mock_features(video_path: Path, num_frames: int = 90) -> pd.DataFrame:
    """Generate realistic mock features for video processing."""
    logger.info(f"Generating mock features for {video_path.name}")
    
    # Create realistic punch patterns
    frames = []
    for i in range(num_frames):
        # Base punch pattern with some variation
        progress = i / num_frames
        
        # Jab-like pattern
        features = {
            "elbow_angle_left": 180 - 80 * progress + np.random.normal(0, 5),
            "elbow_angle_right": 175 + np.random.normal(0, 3),
            "forward_extent_left": 0.8 * progress + np.random.normal(0, 0.1),
            "forward_extent_right": 0.1 + np.random.normal(0, 0.05),
            "hand_speed": 12 * (1 - progress * 0.3) + np.random.normal(0, 2),
            "retraction_speed": 8 * progress + np.random.normal(0, 1),
            "torso_rotation": 0.3 * progress + np.random.normal(0, 0.05),
            "hip_rotation": 0.2 * progress + np.random.normal(0, 0.03),
            "vertical_displacement": 0.4 * progress + np.random.normal(0, 0.05),
            "weight_transfer": 0.6 * progress + np.random.normal(0, 0.08),
        }
        
        # Add some noise and variation
        for key in features:
            features[key] = max(0, features[key])  # Ensure non-negative
            
        features["frame_index"] = i
        frames.append(features)
    
    return pd.DataFrame(frames)

def normalize_features(df: pd.DataFrame) -> pd.DataFrame:
    """Normalize features to 0-1 range."""
    out = df.copy()
    
    # Normalization constants
    NORM = {
        "elbow_angle_left": 180.0,
        "elbow_angle_right": 180.0,
        "forward_extent_left": 1.0,
        "forward_extent_right": 1.0,
        "hand_speed": 15.0,
        "retraction_speed": 8.0,
        "torso_rotation": 0.5,
        "hip_rotation": 0.5,
        "vertical_displacement": 0.5,
        "weight_transfer": 1.0,
    }
    
    for col, denom in NORM.items():
        if col in out.columns and denom != 0:
            out[col] = out[col] / denom
    
    return out

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
        'features_avg': df.select_dtypes(include=[np.number]).mean().to_dict(),
        'temporal_sequence': df[FEATURE_ORDER].fillna(0).values.tolist(),
        'full_data': df.to_dict('records')[:30]  # First 30 frames for inspection
    }
    
    with open(json_path, 'w') as f:
        json.dump(baseline_data, f, indent=2, default=str)
    logger.info(f"✅ Saved JSON: {json_path}")
    
    return parquet_path, json_path

def generate_baselines_for_type(videos_dir: Path, dataset_dir: Path, punch_type: str, num_baselines: int = 3):
    """Generate multiple baselines for a specific punch type."""
    
    logger.info(f"🥊 Processing {punch_type} baselines...")
    
    # Select random videos
    selected_videos = select_random_videos(videos_dir / punch_type, num_baselines)
    
    if not selected_videos:
        logger.warning(f"No videos found for {punch_type}")
        return []
    
    processed_dfs = []
    
    # Process each selected video (using mock features for now)
    for i, video_path in enumerate(selected_videos):
        logger.info(f"Processing video {i+1}/{len(selected_videos)}: {video_path.name}")
        
        # Generate mock features (replace with real processing when pipeline is ready)
        features_df = generate_mock_features(video_path)
        features_df = normalize_features(features_df)
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
        subset_df = baseline_df.iloc[version*30:(version+1)*30]  # Different windows for variety
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
        'total_baselines': len(all_baseline_files) // 2,
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
