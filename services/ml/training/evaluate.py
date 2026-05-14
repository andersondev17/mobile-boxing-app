"""Evaluate trained Random Forest Classifier."""

from __future__ import annotations

import logging
from pathlib import Path

import joblib
from sklearn.metrics import classification_report, accuracy_score, confusion_matrix

from services.ml.training.dataset_builder import build_dataset

logger = logging.getLogger(__name__)

def evaluate(dataset_parquet: Path, model_path: Path) -> None:
    if not model_path.exists():
        logger.error("Model not found at %s", model_path)
        return
        
    pipeline = joblib.load(model_path)
    X, y = build_dataset(dataset_parquet)
    
    y_pred = pipeline.predict(X)
    
    # Accuracy
    acc = accuracy_score(y, y_pred)
    logger.info("Global Accuracy: %.2f%%", acc * 100)
    
    # Precision / Recall per class
    report = classification_report(y, y_pred, output_dict=False)
    logger.info("\nClassification Report:\n%s", report)
    
    # Confusion Matrix
    cm = confusion_matrix(y, y_pred, labels=pipeline.classes_)
    logger.info("\nConfusion Matrix:\n%s", cm)
    logger.info("Classes: %s", pipeline.classes_)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    evaluate(
        Path("build_baseline/dataset/baseline_final.parquet"),
        Path("ml_service/models/punch_classifier.joblib")
    )







