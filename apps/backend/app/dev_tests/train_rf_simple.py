#!/usr/bin/env python3
"""
Simple Random Forest Trainer - Punch Type Classification

Trains RF classifier using baseline data with synthetic augmentation.
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

def create_simple_features(df: pd.DataFrame) -> pd.DataFrame:
    """Create simple features from baseline data."""
    feature_cols = [
        'elbow_angle_left', 'elbow_angle_right',
        'forward_extent_left', 'forward_extent_right', 
        'hand_speed', 'retraction_speed',
        'torso_rotation', 'hip_rotation',
        'vertical_displacement', 'weight_transfer'
    ]
    
    # Group by baseline file
    grouped = df.groupby('baseline_file')
    
    aggregated = []
    for name, group in grouped:
        if len(group) < 5:
            continue
            
        features = {}
        
        # Basic statistics for each feature
        for col in feature_cols:
            if col in group.columns:
                features[f'{col}_mean'] = group[col].mean()
                features[f'{col}_std'] = group[col].std()
                features[f'{col}_max'] = group[col].max()
                features[f'{col}_min'] = group[col].min()
        
        # Target label
        features['punch_type'] = group['punch_type'].iloc[0]
        
        aggregated.append(features)
    
    return pd.DataFrame(aggregated)

def train_classifier(X: pd.DataFrame, y: pd.Series) -> RandomForestClassifier:
    """Train Random Forest classifier."""
    # Remove non-numeric columns and target
    feature_cols = [col for col in X.columns if col != 'punch_type' and col != 'baseline_file']
    X_train = X[feature_cols].fillna(0)
    
    rf = RandomForestClassifier(
        n_estimators=50,  # Reduced for simplicity
        max_depth=8,
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
    
    # Log feature importance
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
    
    # Extract simple features
    logger.info("📊 Extracting simple features...")
    aggregated_data = create_simple_features(raw_data)
    
    if len(aggregated_data) < 10:
        logger.error("❌ Insufficient training data")
        return
    
    # Prepare training data
    feature_cols = [col for col in aggregated_data.columns if col != 'punch_type']
    X = aggregated_data[feature_cols].fillna(0)
    y = aggregated_data['punch_type']
    
    # Use all data for training (small dataset)
    X_train = X
    y_train = y
    
    logger.info(f"🏋 Training with {len(X_train)} samples")
    
    # Train classifier
    logger.info("🤖 Training Random Forest...")
    rf = train_classifier(X_train, y_train)
    
    # Simple validation using cross-validation
    from sklearn.model_selection import cross_val_score
    cv_scores = cross_val_score(rf, X, y, cv=3)  # 3-fold CV
    logger.info(f"📈 Cross-validation scores: {cv_scores}")
    logger.info(f"📈 Mean CV accuracy: {cv_scores.mean():.3f}")
    
    # Print results
    logger.info("🎯 Training Results:")
    logger.info(f"  Classes: {rf.classes_.tolist()}")
    logger.info(f"  Mean CV Accuracy: {cv_scores.mean():.3f}")
    
    # Simple class distribution
    class_counts = y_train.value_counts().to_dict()
    for class_name, count in class_counts.items():
        logger.info(f"  {class_name}: {count} samples")
    
    # Save model and metrics
    training_metrics = {
        'classes': rf.classes_.tolist(),
        'feature_importance': dict(zip(feature_cols, rf.feature_importances_))
    }
    save_model_and_metrics(rf, training_metrics, output_dir)
    
    logger.info("🚀 Random Forest training complete!")

if __name__ == "__main__":
    main()
