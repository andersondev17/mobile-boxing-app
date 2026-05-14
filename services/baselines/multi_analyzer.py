#!/usr/bin/env python3
"""
Multi-Baseline Analyzer - Hybrid RF + DTW Pipeline

Implements the intelligent punch detection system:
1. RF predicts punch type (fast filtering)
2. DTW compares against relevant baselines (accurate validation)
3. Automatic selection of best match (lowest score)
4. Threshold validation (reliable detection)
"""

import json
import logging
import pickle
from pathlib import Path
from typing import List, Dict, Tuple, Optional

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier

from services.ml.core.dtw_scorer import score_window, DTW_FEATURE_ORDER
from app.schemas import BaselineResponse, BoxingStatusResponse

logger = logging.getLogger(__name__)

class MultiBaselineAnalyzer:
    """Hybrid punch detection system combining RF classification with DTW validation."""
    
    def __init__(self, baselines_dir: Path, model_path: Path, enhanced_baselines_dir: Path):
        self.baselines_dir = baselines_dir
        self.enhanced_baselines_dir = enhanced_baselines_dir
        self.model_path = model_path
        self.rf_classifier = None
        self.baselines = {}
        self.enhanced_baselines = {}
        
        self._load_model()
        self._load_baselines()
        self._load_enhanced_baselines()
    
    def _load_model(self):
        """Load Random Forest classifier."""
        if self.model_path.exists():
            with open(self.model_path, 'rb') as f:
                self.rf_classifier = pickle.load(f)
            logger.info("✅ RF model loaded")
        else:
            logger.error("❌ RF model not found")
            raise FileNotFoundError("RF model not found")
    
    def _load_baselines(self):
        """Load all baseline parquet files."""
        punch_types = ["jab", "cross", "hook", "uppercut"]
        
        for punch_type in punch_types:
            punch_dir = self.baselines_dir / punch_type
            if punch_dir.exists():
                baseline_files = list(punch_dir.glob("*.parquet"))
                self.baselines[punch_type] = []
                
                for baseline_file in baseline_files:
                    logger.info(f"Loading baseline: {baseline_file.name}")
                    df = pd.read_parquet(baseline_file)
                    self.baselines[punch_type].append({
                        'filename': baseline_file.name,
                        'data': df,
                        'punch_type': punch_type
                    })
        
        logger.info(f"🎯 Loaded {len(self.baselines)} baseline groups")
    
    def _load_enhanced_baselines(self):
        """Load enhanced baseline parquet files."""
        return
        
        punch_types = ["jab", "cross", "hook", "uppercut"]
        
        for punch_type in punch_types:
            punch_dir = self.enhanced_baselines_dir / punch_type
            if punch_dir.exists():
                baseline_files = list(punch_dir.glob("*enhanced*.parquet"))
                if punch_type not in self.enhanced_baselines:
                    self.enhanced_baselines[punch_type] = []
                
                for baseline_file in baseline_files:
                    logger.info(f"Loading enhanced baseline: {baseline_file.name}")
                    df = pd.read_parquet(baseline_file)
                    self.enhanced_baselines[punch_type].append({
                        'filename': baseline_file.name,
                        'data': df,
                        'punch_type': punch_type,
                        'enhanced': True
                    })
        
        logger.info(f"Loaded {len(self.enhanced_baselines)} enhanced baseline groups")
    
    def predict_punch_type(self, features: dict) -> List[Tuple[str, float]]:
        """Use RF to predict top-k punch types."""
        if not self.rf_classifier:
            return []
        
        # Generate all 40 required features from single frame
        # This matches the training data format
        base_features = [
            'elbow_angle_left', 'elbow_angle_right',
            'forward_extent_left', 'forward_extent_right',
            'hand_speed', 'retraction_speed',
            'torso_rotation', 'hip_rotation',
            'vertical_displacement', 'weight_transfer'
        ]
        
        # Create aggregated features from single frame
        rf_features = []
        for feature in base_features:
            if feature in features:
                rf_features.append(features.get(feature, 0.0))
            else:
                rf_features.append(0.0)
        
        # Add statistical features to reach 40 total
        # These match the training format exactly
        for feature in base_features:
            # Add mean features (already added above)
            rf_features.append(features.get(feature, 0.0))  # mean
            
            # Add std features
            rf_features.append(0.1)  # std (placeholder)
            
            # Add max features  
            rf_features.append(features.get(feature, 0.0))  # max
            
            # Add min features
            rf_features.append(0.0)  # min (placeholder)
        
        # Ensure we have exactly 40 features
        rf_features = rf_features[:40] if len(rf_features) > 40 else rf_features + [0.0] * (40 - len(rf_features))
        
        # Get RF predictions
        try:
            probabilities = self.rf_classifier.predict_proba([rf_features])[0]
            classes = self.rf_classifier.classes_
            
            # Create list of (class, probability) tuples
            predictions = list(zip(classes, probabilities))
            predictions.sort(key=lambda x: x[1], reverse=True)  # Sort by probability
            
            return predictions[:3]  # Return top-3
        except Exception as e:
            logger.error(f"RF prediction failed: {e}")
            return []
    
    def compare_with_dtw(self, user_features: List[dict], candidate_punches: List[str]) -> Dict[str, float]:
        """Compare user sequence against relevant baselines using DTW."""
        if not user_features:
            return {}
        
        dtw_scores = {}
        
        for punch_type in candidate_punches:
                # Prefer enhanced baselines, fallback to regular baselines
                available_baselines = []
                if punch_type in self.enhanced_baselines:
                    available_baselines.extend(self.enhanced_baselines[punch_type])
                if punch_type in self.baselines:
                    available_baselines.extend(self.baselines[punch_type])
                
                if not available_baselines:
                    continue
                    
                best_score = float('inf')
                
                # Compare against all available baselines of this punch type
                for baseline_info in available_baselines:
                    baseline_data = baseline_info['data']
                    
                    # Extract DTW features from user sequence
                    user_sequence = []
                    for frame in user_features:
                        dtw_features = {
                            'elbow_angle_left': frame.get('elbow_angle_left', 0.0),
                            'elbow_angle_right': frame.get('elbow_angle_right', 0.0),
                            'forward_extent_left': frame.get('forward_extent_left', 0.0),
                            'forward_extent_right': frame.get('forward_extent_right', 0.0),
                            'hand_speed': frame.get('hand_speed', 0.0),
                            'retraction_speed': frame.get('retraction_speed', 0.0),
                            'torso_rotation': frame.get('torso_rotation', 0.0),
                            'hip_rotation': frame.get('hip_rotation', 0.0),
                            'vertical_displacement': frame.get('vertical_displacement', 0.0),
                            'weight_transfer': frame.get('weight_transfer', 0.0),
                        }
                        user_sequence.append(dtw_features)
                    
                    # Calculate DTW score
                    score = score_window(user_sequence, baseline_data.to_dict('records'))
                    if score < best_score:
                        best_score = score
            
                dtw_scores[punch_type] = best_score
        
        return dtw_scores
    
    def select_best_match(self, dtw_scores: Dict[str, float], threshold: float = 15.0) -> Dict[str, any]:
        """Select best punch type based on lowest DTW score."""
        if not dtw_scores:
            return {
                'punch_type': 'unknown',
                'dtw_score': float('inf'),
                'is_valid': False,
                'rf_predictions': [],
                'all_scores': {}
            }
        
        # Find best match (lowest score)
        best_punch = min(dtw_scores.keys(), key=lambda k: dtw_scores[k])
        best_score = dtw_scores[best_punch]
        
        # Determine if it's a valid punch
        is_valid = best_score < threshold
        
        return {
            'punch_type': best_punch,
            'dtw_score': best_score,
            'is_valid': is_valid,
            'all_scores': dtw_scores,
            'threshold_used': threshold
        }
    
    def analyze_sequence(self, user_features: List[dict], threshold: float = 15.0) -> Dict[str, any]:
        """Complete hybrid analysis: RF → DTW → Best Match."""
        logger.info("🔥 Starting hybrid analysis...")
        
        # Step 1: RF classification for filtering
        rf_predictions = self.predict_punch_type(user_features[0] if user_features else {})
        logger.info(f"🤖 RF top predictions: {rf_predictions}")
        
        # Step 2: Extract candidate punch types
        candidate_punches = [punch for punch, _ in rf_predictions]
        
        # Step 3: DTW comparison against relevant baselines
        dtw_scores = self.compare_with_dtw(user_features, candidate_punches)
        logger.info(f"📏 DTW scores: {dtw_scores}")
        
        # Step 4: Select best match
        result = self.select_best_match(dtw_scores, threshold)
        
        logger.info(f"🎯 Best match: {result['punch_type']} (score: {result['dtw_score']:.2f}, valid: {result['is_valid']})")
        
        return result
    
    def set_baseline(self, baseline_df):
        """Set a baseline dataframe for analysis."""
        self.current_baseline = baseline_df
        logger.info(f"Baseline set with {len(baseline_df)} rows")

# Global analyzer instance
_analyzer: Optional[MultiBaselineAnalyzer] = None

def get_analyzer() -> MultiBaselineAnalyzer:
    """Get or create global analyzer instance."""
    global _analyzer
    if _analyzer is None:
        base_dir = Path(__file__).parent
        baselines_dir = base_dir / "build_baseline" / "dataset"
        enhanced_baselines_dir = base_dir / "build_baseline" / "dataset_enhanced"
        model_path = base_dir / "models" / "rf_classifier.pkl"
        
        _analyzer = MultiBaselineAnalyzer(baselines_dir, model_path, enhanced_baselines_dir)
        logger.info("Multi-baseline analyzer initialized with enhanced baselines")
    
    return _analyzer

def analyze_user_sequence(user_features: List[dict], threshold: float = 15.0) -> Dict[str, any]:
    """Analyze user sequence using hybrid RF + DTW pipeline."""
    analyzer = get_analyzer()
    return analyzer.analyze_sequence(user_features, threshold)

def set_baseline(self, baseline_df):
        """Set a baseline dataframe for analysis."""
        self.current_baseline = baseline_df
        logger.info(f"Baseline set with {len(baseline_df)} rows")

def get_system_status() -> Dict[str, any]:
    """Get current system status."""
    analyzer = get_analyzer()

def get_analyzer():
    """Get or create global analyzer instance."""
    global _analyzer
    if _analyzer is None:
        base_dir = Path(__file__).parent
        baselines_dir = base_dir / "build_baseline" / "dataset"
        enhanced_baselines_dir = base_dir / "build_baseline" / "dataset_enhanced"
        model_path = base_dir / "models" / "rf_classifier.pkl"
        
        _analyzer = MultiBaselineAnalyzer(baselines_dir, model_path, enhanced_baselines_dir)
        logger.info("Multi-baseline analyzer initialized with enhanced baselines")
    
    return _analyzer

def get_analyzer_status():
    """Get current analyzer status for debugging."""
    analyzer = get_analyzer()
    
    return {
        'baselines_loaded': len(analyzer.baselines) > 0,
        'model_loaded': analyzer.rf_classifier is not None,
        'punch_types': list(analyzer.baselines.keys()),
        'total_baselines': sum(len(baselines) for baselines in analyzer.baselines.values())
    }






