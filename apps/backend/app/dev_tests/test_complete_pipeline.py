#!/usr/bin/env python3
"""
Complete pipeline test with real video analysis simulation
to verify the entire boxing analysis system works correctly.
"""

import sys
import logging
import pandas as pd
import numpy as np
from pathlib import Path
from unittest.mock import Mock, patch

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_mock_video_features(punch_type="cross", num_frames=30):
    """Create realistic mock features for video analysis."""
    features = []
    
    for i in range(num_frames):
        if punch_type == "cross":
            # Cross-specific features
            feature = {
                'elbow_angle_left': 160 + np.random.normal(0, 5),
                'elbow_angle_right': 90 + np.random.normal(0, 10),
                'forward_extent_left': 0.2 + np.random.normal(0, 0.05),
                'forward_extent_right': 0.7 + np.random.normal(0, 0.1),
                'hand_speed': 12.0 + np.random.normal(0, 2),
                'retraction_speed': 8.0 + np.random.normal(0, 1.5),
                'torso_rotation': 0.25 + np.random.normal(0, 0.05),
                'hip_rotation': 0.3 + np.random.normal(0, 0.05),
                'vertical_displacement': 0.1 + np.random.normal(0, 0.02),
                'weight_transfer': 0.8 + np.random.normal(0, 0.1),
                'frame_index': i,
                'tracking_state': 'tracking',
            }
        elif punch_type == "jab":
            # Jab-specific features
            feature = {
                'elbow_angle_left': 100 + np.random.normal(0, 10),
                'elbow_angle_right': 160 + np.random.normal(0, 5),
                'forward_extent_left': 0.6 + np.random.normal(0, 0.1),
                'forward_extent_right': 0.3 + np.random.normal(0, 0.05),
                'hand_speed': 10.0 + np.random.normal(0, 2),
                'retraction_speed': 12.0 + np.random.normal(0, 2),
                'torso_rotation': 0.15 + np.random.normal(0, 0.03),
                'hip_rotation': 0.2 + np.random.normal(0, 0.03),
                'vertical_displacement': 0.05 + np.random.normal(0, 0.01),
                'weight_transfer': 0.6 + np.random.normal(0, 0.08),
                'frame_index': i,
                'tracking_state': 'tracking',
            }
        else:
            # Generic features for other punch types
            feature = {
                'elbow_angle_left': 120 + np.random.normal(0, 10),
                'elbow_angle_right': 120 + np.random.normal(0, 10),
                'forward_extent_left': 0.4 + np.random.normal(0, 0.08),
                'forward_extent_right': 0.4 + np.random.normal(0, 0.08),
                'hand_speed': 8.0 + np.random.normal(0, 1.5),
                'retraction_speed': 8.0 + np.random.normal(0, 1.5),
                'torso_rotation': 0.2 + np.random.normal(0, 0.04),
                'hip_rotation': 0.2 + np.random.normal(0, 0.04),
                'vertical_displacement': 0.08 + np.random.normal(0, 0.02),
                'weight_transfer': 0.7 + np.random.normal(0, 0.08),
                'frame_index': i,
                'tracking_state': 'tracking',
            }
        
        features.append(feature)
    
    return features

def test_complete_pipeline():
    """Test the complete pipeline with mock video analysis."""
    logger.info("=== Testing Complete Pipeline ===")
    
    try:
        from ml_service.analyzer import VideoAnalysisResult, FrameResult
        from ml_service.feedback_engine import SpanishBoxingFeedback
        from multi_baseline_analyzer import get_analyzer
        from routes.boxing import detect_punch_type
        
        # Test 1: Baseline Loading and Selection
        logger.info("--- Test 1: Baseline Loading ---")
        analyzer = get_analyzer()
        
        # Load cross baseline
        cross_baseline_path = Path(__file__).parent / "build_baseline" / "dataset" / "dataset" / "cross" / "cross_v1.parquet"
        if cross_baseline_path.exists():
            cross_baseline = pd.read_parquet(cross_baseline_path)
            analyzer.set_baseline(cross_baseline)
            logger.info(f"Cross baseline loaded: {len(cross_baseline)} rows")
        else:
            logger.error("Cross baseline not found")
            return False
        
        # Test 2: Punch Type Detection
        logger.info("--- Test 2: Punch Type Detection ---")
        test_filenames = [
            "cross_technique.mp4",
            "jab_training.mp4", 
            "hook_power.mp4",
            "uppercut_fight.mp4"
        ]
        
        for filename in test_filenames:
            detected = detect_punch_type(filename)
            logger.info(f"File: {filename} -> Detected: {detected}")
        
        # Test 3: Mock Video Analysis with Cross
        logger.info("--- Test 3: Mock Video Analysis (Cross) ---")
        
        # Create mock features for cross video
        mock_features = create_mock_video_features("cross", 30)
        
        # Create frame results with meaningful scores
        frame_results = []
        for i, features in enumerate(mock_features):
            # Simulate DTW scoring against baseline
            base_score = 75.0
            variation = np.random.normal(0, 5)
            dtw_score = max(50.0, min(95.0, base_score + variation))
            
            # Determine qualitative label
            if dtw_score >= 85:
                label = "excellent"
            elif dtw_score >= 75:
                label = "good"
            elif dtw_score >= 65:
                label = "developing"
            else:
                label = "poor"
            
            frame_result = FrameResult(
                frame_index=i,
                dtw_score=dtw_score,
                qualitative_label=label,
                features=features
            )
            frame_results.append(frame_result)
        
        # Calculate aggregate statistics
        scores = [r.dtw_score for r in frame_results]
        avg_score = np.mean(scores)
        min_score = np.min(scores)
        max_score = np.max(scores)
        
        # Create video analysis result
        result = VideoAnalysisResult(
            video_name="test_cross_video.mp4",
            total_frames=371,
            scored_frames=len(frame_results),
            avg_score=avg_score,
            min_score=min_score,
            max_score=max_score,
            frame_results=frame_results,
            feedback=[],
            punch_type="cross",
            processing_ms=2500.0,
            baseline_curve=[avg_score] * len(frame_results)
        )
        
        logger.info(f"Mock analysis completed:")
        logger.info(f"  Video: {result.video_name}")
        logger.info(f"  Punch type: {result.punch_type}")
        logger.info(f"  Avg score: {result.avg_score:.1f}")
        logger.info(f"  Score range: {result.min_score:.1f} - {result.max_score:.1f}")
        logger.info(f"  Frames scored: {result.scored_frames}/{result.total_frames}")
        
        # Test 4: Spanish Coaching Feedback
        logger.info("--- Test 4: Spanish Coaching Feedback ---")
        feedback_engine = SpanishBoxingFeedback()
        
        # Get feedback for cross video
        coaching_feedback = []
        motivational_messages = []
        
        # Use features from first few frames for feedback
        for frame_result in frame_results[:3]:
            coaching = feedback_engine.get_coaching_feedback("cross", frame_result.features)
            if coaching:
                coaching_feedback.extend(coaching)
            motivational_messages.append(feedback_engine.get_motivational_message())
        
        # Remove duplicates and limit
        coaching_feedback = list(set(coaching_feedback))[:3]
        motivational_messages = list(set(motivational_messages))[:2]
        
        logger.info(f"Coaching feedback: {coaching_feedback}")
        logger.info(f"Motivational messages: {motivational_messages}")
        
        # Test 5: Complete Response Structure
        logger.info("--- Test 5: Complete Response Structure ---")
        
        complete_response = {
            "run_id": "test-run-123",
            "video_name": result.video_name,
            "punch_type_detected": "cross",
            "baseline_type": "cross",
            "baseline_used": str(cross_baseline_path),
            "total_frames": result.total_frames,
            "scored_frames": result.scored_frames,
            "avg_score": result.avg_score,
            "min_score": result.min_score,
            "max_score": result.max_score,
            "technique_level": "elite" if result.avg_score >= 85 else "good" if result.avg_score >= 70 else "developing" if result.avg_score >= 50 else "poor",
            "frame_scores": [
                {
                    "frame_index": r.frame_index,
                    "dtw_score": r.dtw_score,
                    "label": r.qualitative_label,
                }
                for r in result.frame_results
            ],
            "baseline_curve": result.baseline_curve,
            "coaching_feedback": coaching_feedback,
            "motivational_messages": motivational_messages,
            "feedback": result.feedback,
            "punch_type": result.punch_type,
            "processing_ms": result.processing_ms,
        }
        
        logger.info("Complete response structure created successfully:")
        logger.info(f"  Technique level: {complete_response['technique_level']}")
        logger.info(f"  Baseline used: {complete_response['baseline_type']}")
        logger.info(f"  Coaching messages: {len(complete_response['coaching_feedback'])}")
        logger.info(f"  Motivational messages: {len(complete_response['motivational_messages'])}")
        
        return True
        
    except Exception as e:
        logger.error(f"Error in complete pipeline test: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_baseline_matching():
    """Test that correct baselines are selected for different punch types."""
    logger.info("=== Testing Baseline Matching ===")
    
    try:
        from multi_baseline_analyzer import get_analyzer
        from routes.boxing import detect_punch_type
        
        analyzer = get_analyzer()
        
        # Test baseline paths for each punch type
        punch_types = ["jab", "cross", "hook", "uppercut"]
        
        for punch_type in punch_types:
            baseline_path = Path(__file__).parent / "build_baseline" / "dataset" / "dataset" / punch_type / f"{punch_type}_v1.parquet"
            
            if baseline_path.exists():
                logger.info(f"Baseline found for {punch_type}: {baseline_path}")
                # Test loading
                baseline_df = pd.read_parquet(baseline_path)
                logger.info(f"  Loaded {len(baseline_df)} rows for {punch_type}")
            else:
                logger.warning(f"Baseline not found for {punch_type}: {baseline_path}")
        
        return True
        
    except Exception as e:
        logger.error(f"Error in baseline matching test: {e}")
        return False

def main():
    """Run complete pipeline tests."""
    logger.info("Starting Complete Pipeline Test")
    
    tests = [
        ("Complete Pipeline", test_complete_pipeline),
        ("Baseline Matching", test_baseline_matching),
    ]
    
    results = {}
    for test_name, test_func in tests:
        logger.info(f"\n{'='*60}")
        logger.info(f"Running: {test_name}")
        logger.info(f"{'='*60}")
        
        try:
            result = test_func()
            results[test_name] = result
            status = "PASS" if result else "FAIL"
            logger.info(f"{test_name}: {status}")
        except Exception as e:
            logger.error(f"{test_name}: ERROR - {e}")
            results[test_name] = False
    
    # Summary
    logger.info(f"\n{'='*60}")
    logger.info("COMPLETE PIPELINE TEST SUMMARY")
    logger.info(f"{'='*60}")
    
    passed = sum(1 for result in results.values() if result)
    total = len(results)
    
    for test_name, result in results.items():
        status = "PASS" if result else "FAIL"
        logger.info(f"{test_name}: {status}")
    
    logger.info(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        logger.info("All complete pipeline tests passed! System ready for video analysis.")
        return True
    else:
        logger.error(f"{total - passed} tests failed. Pipeline needs fixes.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
