#!/usr/bin/env python3
"""
Random Forest Trainer - Punch Type Classification

Trains RF classifier to predict punch type from aggregated features.
This enables intelligent filtering before DTW comparison.

Usage:
    python train_rf_classifier.py
"""

import json
import logging
import pickle
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, confusion_matrix

logger = logging.getLogger(__name__)

def load_baselines(dataset_dir: Path) -> pd.DataFrame:
    """Load all baseline data for training."""
    all_data = []
    
    punch_types = ["jab", "cross", "hook", "uppercut"]
    
    for punch_type in punch_types:
        punch_dir = dataset_dir / punch_type
        if not punch_dir.exists():
            logger.warning(f"No baseline directory for {punch_type}")
            continue
            
        # Load all parquet files for this punch type
        parquet_files = list(punch_dir.glob("*.parquet"))
        
        for parquet_file in parquet_files:
            logger.info(f"Loading {parquet_file.name}")
            df = pd.read_parquet(parquet_file)
            
            # Add target label
            df['punch_type'] = punch_type
            df['baseline_file'] = parquet_file.name
            
            all_data.append(df)
    
    if not all_data:
        raise ValueError("No baseline data found")
    
    combined = pd.concat(all_data, ignore_index=True)
    logger.info(f"Loaded {len(combined)} total training samples")
    
    return combined

def extract_aggregated_features(df: pd.DataFrame) -> pd.DataFrame:
    """Extract aggregated features from raw frame data."""
    feature_cols = [
        'elbow_angle_left', 'elbow_angle_right',
        'forward_extent_left', 'forward_extent_right', 
        'hand_speed', 'retraction_speed',
        'torso_rotation', 'hip_rotation',
        'vertical_displacement', 'weight_transfer'
    ]
    
    # Group by sequence/baseline to get aggregated features
    # Assuming each baseline has a unique identifier
    if 'baseline_file' in df.columns:
        grouped = df.groupby('baseline_file')
    else:
        # If no baseline_file, create groups manually
        df['group_id'] = (df.index // 30)  # Assume 30 frames per sequence
        grouped = df.groupby('group_id')
    
    aggregated = []
    
    for name, group in grouped:
        if len(group) < 10:  # Skip very short sequences
            continue
            
        features = {}
        
        # Basic statistics
        for col in feature_cols:
            if col in group.columns:
                features[f'{col}_mean'] = group[col].mean()
                features[f'{col}_std'] = group[col].std()
                features[f'{col}_max'] = group[col].max()
                features[f'{col}_min'] = group[col].min()
        
        # Temporal features
        if 'hand_speed' in group.columns:
            speeds = group['hand_speed'].values
            if len(speeds) > 1:
                features['speed_acceleration'] = np.diff(speeds).mean()
                features['speed_variance'] = np.var(speeds)
        
        if 'forward_extent_left' in group.columns:
            extensions = group['forward_extent_left'].values
            if len(extensions) > 1:
                features['extension_rate'] = np.diff(extensions).mean()
        
        # Range of motion
        for col in ['elbow_angle_left', 'torso_rotation']:
            if col in group.columns:
                values = group[col].values
                features[f'{col}_range'] = np.max(values) - np.min(values)
        
        # Target label
        features['punch_type'] = group['punch_type'].iloc[0]
        
        aggregated.append(features)
    
    # Generate synthetic variations to increase dataset size
    synthetic_data = []
    for _, row in aggregated.itertuples():
        # Create 5 synthetic variations per real sample
        for i in range(5):
            synth_row = row.copy()
            
            # Add noise to numerical features
            for col in feature_cols:
                if f'{col}_mean' in row:
                    noise_factor = np.random.uniform(0.9, 1.1)  # ±10% variation
                    synth_row[f'{col}_mean'] = row[f'{col}_mean'] * noise_factor
                    synth_row[f'{col}_std'] = row[f'{col}_std'] * np.random.uniform(0.8, 1.2)
            
            synthetic_data.append(synth_row)
    
    # Combine real + synthetic data
    final_data = pd.concat([pd.DataFrame(aggregated), pd.DataFrame(synthetic_data)], ignore_index=True)
    
    return final_data

def train_classifier(X: pd.DataFrame, y: pd.Series) -> RandomForestClassifier:
    """Train Random Forest classifier."""
    # Remove non-numeric columns and target
    feature_cols = [col for col in X.columns if col != 'punch_type' and col != 'baseline_file']
    X_train = X[feature_cols].fillna(0)
    
    rf = RandomForestClassifier(
        n_estimators=100,
        max_depth=10,
        min_samples_split=5,
        min_samples_leaf=2,
        random_state=42,
        n_jobs=-1
    )
    
    rf.fit(X_train, y)
    return rf

def evaluate_classifier(rf: RandomForestClassifier, X_test: pd.DataFrame, y_test: pd.Series) -> dict:
    """Evaluate classifier and return metrics."""
    feature_cols = [col for col in X_test.columns if col != 'punch_type' and col != 'baseline_file']
    X_test_clean = X_test[feature_cols].fillna(0)
    
    y_pred = rf.predict(X_test_clean)
    y_proba = rf.predict_proba(X_test_clean)
    
    # Classification report
    report = classification_report(y_test, y_pred, output_dict=True)
    
    # Confusion matrix
    cm = confusion_matrix(y_test, y_pred, labels=rf.classes_)
    
    return {
        'classification_report': report,
        'confusion_matrix': cm.tolist(),
        'classes': rf.classes_.tolist(),
        'feature_importance': dict(zip(feature_cols, rf.feature_importances_))
    }

def save_model_and_metrics(rf: RandomForestClassifier, metrics: dict, output_dir: Path):
    """Save trained model and evaluation metrics."""
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Save model
    model_path = output_dir / "rf_classifier.pkl"
    with open(model_path, 'wb') as f:
        pickle.dump(rf, f)
    logger.info(f"✅ Model saved: {model_path}")
    
    # Save metrics
    metrics_path = output_dir / "training_metrics.json"
    with open(metrics_path, 'w') as f:
        json.dump(metrics, f, indent=2, default=str)
    logger.info(f"✅ Metrics saved: {metrics_path}")
    
    # Feature importance logging (no plotting)
    if 'feature_importance' in metrics:
        importance_data = sorted(metrics['feature_importance'].items(), key=lambda x: x[1], reverse=True)
        logger.info("📊 Top 10 Important Features:")
        for i, (feature, importance) in enumerate(importance_data[:10]):
            logger.info(f"  {i+1}. {feature}: {importance:.4f}")

def main():
    """Main training pipeline."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    base_dir = Path(__file__).parent
    dataset_dir = base_dir / "dataset"
    output_dir = base_dir / "models"
    
    logger.info("🌲 Starting Random Forest training...")
    
    # Load baseline data
    try:
        raw_data = load_baselines(dataset_dir)
    except Exception as e:
        logger.error(f"❌ Failed to load baseline data: {e}")
        return
    
    # Extract aggregated features
    logger.info("📊 Extracting aggregated features...")
    aggregated_data = extract_aggregated_features(raw_data)
    
    if len(aggregated_data) < 20:
        logger.error("❌ Insufficient training data")
        return
    
    # Prepare training data
    feature_cols = [col for col in aggregated_data.columns if col != 'punch_type']
    X = aggregated_data[feature_cols].fillna(0)
    y = aggregated_data['punch_type']
    
    # Split data
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    
    logger.info(f"🏋 Training with {len(X_train)} samples, testing with {len(X_test)} samples")
    
    # Train classifier
    logger.info("🤖 Training Random Forest...")
    rf = train_classifier(X_train, y_train)
    
    # Evaluate
    logger.info("📈 Evaluating classifier...")
    metrics = evaluate_classifier(rf, X_test, y_test)
    
    # Print results
    logger.info("🎯 Training Results:")
    logger.info(f"  Classes: {metrics['classes']}")
    logger.info(f"  Accuracy: {metrics['classification_report']['accuracy']:.3f}")
    
    for class_name in metrics['classes']:
        if class_name in metrics['classification_report']:
            class_metrics = metrics['classification_report'][class_name]
            logger.info(f"  {class_name}:")
            logger.info(f"    Precision: {class_metrics['precision']:.3f}")
            logger.info(f"    Recall: {class_metrics['recall']:.3f}")
            logger.info(f"    F1-score: {class_metrics['f1-score']:.3f}")
    
    # Save model and metrics
    save_model_and_metrics(rf, metrics, output_dir)
    
    logger.info("🚀 Random Forest training complete!")

if __name__ == "__main__":
    main()
