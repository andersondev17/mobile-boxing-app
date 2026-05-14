"""
Hybrid Random Forest + DTW Punch Classifier

This service implements the hybrid approach where:
1. Random Forest provides fast initial filtering (top-k predictions)
2. DTW performs fine-grained validation against selected baselines
3. Final decision combines both approaches for optimal accuracy and speed
"""

import json
import logging
import pickle
from pathlib import Path
from typing import List, Dict, Tuple, Optional
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from scipy.spatial.distance import euclidean
from fastdtw import fastdtw

from app.schemas import settings

logger = logging.getLogger(__name__)

class HybridPunchClassifier:
    """
    Hybrid classifier combining Random Forest filtering with DTW validation.
    
    Architecture:
    Features -> RF (classification) -> top-k punch types
             -> DTW -> validation against selected baselines
             -> final decision with confidence scores
    """
    
    def __init__(self, 
                 rf_model_path: Optional[str] = None,
                 baseline_path: Optional[str] = None):
        """
        Initialize the hybrid classifier.
        
        Args:
            rf_model_path: Path to trained Random Forest model
            baseline_path: Path to baseline parquet file
        """
        self.rf_model = None
        self.baselines = None
        self.punch_types = ["jab", "cross", "hook", "uppercut"]
        
        # Load models and baselines
        self._load_rf_model(rf_model_path)
        self._load_baselines(baseline_path)
        
    def _load_rf_model(self, model_path: Optional[str]) -> None:
        """Load the trained Random Forest model."""
        if not model_path:
            model_path = Path(__file__).parent.parent / "models" / "rf_classifier.pkl"
        
        try:
            with open(model_path, 'rb') as f:
                self.rf_model = pickle.load(f)
            logger.info(f"Loaded RF model from {model_path}")
        except FileNotFoundError:
            logger.warning(f"RF model not found at {model_path}. Using fallback classification.")
            self.rf_model = None
            
    def _load_baselines(self, baseline_path: Optional[str]) -> None:
        """Load baseline data for DTW comparison."""
        if not baseline_path:
            baseline_path = Path(__file__).parent.parent / "dataset" / "baseline_final.parquet"
        
        try:
            self.baselines = pd.read_parquet(baseline_path)
            logger.info(f"Loaded {len(self.baselines)} baseline samples from {baseline_path}")
        except FileNotFoundError:
            logger.warning(f"Baseline file not found at {baseline_path}. DTW validation disabled.")
            self.baselines = None
    
    def extract_features(self, landmarks: List[Dict]) -> Dict:
        """
        Extract aggregated features from landmark sequence for RF classification.
        
        Args:
            landmarks: List of landmark dictionaries
            
        Returns:
            Dictionary of aggregated features
        """
        if not landmarks:
            return {}
            
        df = pd.DataFrame(landmarks)
        features = {}
        
        # Key biomechanical features
        feature_cols = [
            'elbow_angle_left', 'elbow_angle_right',
            'forward_extent_left', 'forward_extent_right', 
            'hand_speed', 'retraction_speed',
            'torso_rotation', 'hip_rotation',
            'vertical_displacement', 'weight_transfer'
        ]
        
        # Extract statistics for each feature
        for col in feature_cols:
            if col in df.columns:
                features[f'{col}_mean'] = df[col].mean()
                features[f'{col}_std'] = df[col].std()
                features[f'{col}_max'] = df[col].max()
                features[f'{col}_min'] = df[col].min()
        
        # Add temporal features
        if 'hand_speed' in df.columns:
            speeds = df['hand_speed'].values
            if len(speeds) > 1:
                features['speed_acceleration'] = np.diff(speeds).mean()
                features['speed_variance'] = np.var(speeds)
        
        # Add trajectory features
        if 'forward_extent_right' in df.columns:
            trajectory = df['forward_extent_right'].values
            if len(trajectory) > 2:
                # Linearity vs circularity
                linear_fit = np.polyfit(range(len(trajectory)), trajectory, 1)
                features['trajectory_linearity'] = 1.0 - np.std(trajectory - np.polyval(linear_fit, range(len(trajectory))))
        
        return features
    
    def rf_predict_top_k(self, features: Dict, k: int = 2) -> List[Tuple[str, float]]:
        """
        Use Random Forest to get top-k punch predictions.
        
        Args:
            features: Extracted features dictionary
            k: Number of top predictions to return
            
        Returns:
            List of (punch_type, probability) tuples
        """
        if self.rf_model is None:
            # Fallback: return all types with equal probability
            return [(punch_type, 0.25) for punch_type in self.punch_types[:k]]
        
        # Prepare feature vector in the correct order
        feature_names = self.rf_model.feature_names_in_
        X = np.array([features.get(name, 0) for name in feature_names]).reshape(1, -1)
        
        # Get probabilities
        probabilities = self.rf_model.predict_proba(X)[0]
        
        # Get top-k predictions
        top_indices = np.argsort(probabilities)[::-1][:k]
        top_predictions = [
            (self.punch_types[i], probabilities[i]) 
            for i in top_indices
        ]
        
        return top_predictions
    
    def dtw_compare(self, 
                   test_sequence: List[Dict], 
                   punch_type: str, 
                   top_n: int = 3) -> List[Tuple[str, float]]:
        """
        Compare test sequence against baselines using DTW.
        
        Args:
            test_sequence: Test landmark sequence
            punch_type: Type of punch to compare against
            top_n: Number of best matches to return
            
        Returns:
            List of (baseline_id, dtw_score) tuples
        """
        if self.baselines is None:
            return [("baseline_fallback", 0.5)]
        
        # Filter baselines by punch type
        type_baselines = self.baselines[self.baselines['punch_type'] == punch_type]
        
        if len(type_baselines) == 0:
            logger.warning(f"No baselines found for punch type: {punch_type}")
            return [("baseline_fallback", 0.5)]
        
        # Extract test sequence features
        test_df = pd.DataFrame(test_sequence)
        test_features = []
        
        # Use key features for DTW comparison
        key_features = [
            'elbow_angle_right', 'forward_extent_right', 
            'hand_speed', 'torso_rotation'
        ]
        
        for feature in key_features:
            if feature in test_df.columns:
                test_features.append(test_df[feature].values)
            else:
                test_features.append(np.zeros(len(test_sequence)))
        
        test_sequence_features = np.column_stack(test_features)
        
        # Compare against each baseline
        dtw_scores = []
        
        for idx, baseline in type_baselines.iterrows():
            try:
                # Reconstruct baseline sequence
                baseline_features = []
                for feature in key_features:
                    if feature in baseline:
                        baseline_features.append(baseline[feature])
                    else:
                        baseline_features.append(np.zeros(len(test_sequence)))
                
                baseline_sequence = np.column_stack(baseline_features)
                
                # Calculate DTW distance
                distance, _ = fastdtw(
                    test_sequence_features, 
                    baseline_sequence, 
                    dist=euclidean
                )
                
                # Normalize distance (lower is better)
                max_possible_distance = len(test_sequence) * 10  # Rough normalization
                normalized_score = 1.0 - (distance / max_possible_distance)
                normalized_score = max(0, min(1, normalized_score))  # Clamp to [0,1]
                
                dtw_scores.append((f"baseline_{idx}", normalized_score))
                
            except Exception as e:
                logger.warning(f"DTW comparison failed for baseline {idx}: {e}")
                continue
        
        # Sort by score (descending) and return top-n
        dtw_scores.sort(key=lambda x: x[1], reverse=True)
        return dtw_scores[:top_n]
    
    def classify_punch(self, 
                     landmarks: List[Dict], 
                     rf_k: int = 2, 
                     dtw_n: int = 3,
                     min_confidence: float = 0.6) -> Dict:
        """
        Perform hybrid classification of punch sequence.
        
        Args:
            landmarks: List of landmark dictionaries
            rf_k: Number of top RF predictions to consider
            dtw_n: Number of DTW comparisons per RF prediction
            min_confidence: Minimum confidence threshold
            
        Returns:
            Dictionary with classification results
        """
        if not landmarks:
            return {
                "punch_type": "unknown",
                "confidence": 0.0,
                "method": "no_data",
                "details": {}
            }
        
        # Step 1: Extract features
        features = self.extract_features(landmarks)
        
        # Step 2: RF filtering
        rf_predictions = self.rf_predict_top_k(features, k=rf_k)
        logger.info(f"RF top-{rf_k} predictions: {rf_predictions}")
        
        # Step 3: DTW validation for each RF prediction
        dtw_results = {}
        best_overall_score = 0
        best_punch_type = "unknown"
        best_method = "rf_fallback"
        
        for punch_type, rf_confidence in rf_predictions:
            dtw_matches = self.dtw_compare(landmarks, punch_type, top_n=dtw_n)
            dtw_results[punch_type] = {
                "rf_confidence": rf_confidence,
                "dtw_matches": dtw_matches,
                "best_dtw_score": dtw_matches[0][1] if dtw_matches else 0
            }
            
            # Combine RF and DTW scores
            best_dtw_score = dtw_matches[0][1] if dtw_matches else 0
            combined_score = 0.6 * rf_confidence + 0.4 * best_dtw_score
            
            if combined_score > best_overall_score:
                best_overall_score = combined_score
                best_punch_type = punch_type
                best_method = "hybrid"
        
        # Step 4: Final decision
        if best_overall_score < min_confidence:
            best_punch_type = "unknown"
            best_method = "below_threshold"
        
        return {
            "punch_type": best_punch_type,
            "confidence": best_overall_score,
            "method": best_method,
            "details": {
                "rf_predictions": rf_predictions,
                "dtw_results": dtw_results,
                "feature_count": len(features)
            }
        }
    
    def get_feature_importance(self) -> Optional[Dict]:
        """Get feature importance from the Random Forest model."""
        if self.rf_model is None:
            return None
        
        feature_names = self.rf_model.feature_names_in_
        importances = self.rf_model.feature_importances_
        
        return dict(zip(feature_names, importances))

# Global instance for reuse
_hybrid_classifier = None

def get_hybrid_classifier() -> HybridPunchClassifier:
    """Get or create the global hybrid classifier instance."""
    global _hybrid_classifier
    if _hybrid_classifier is None:
        _hybrid_classifier = HybridPunchClassifier()
    return _hybrid_classifier







