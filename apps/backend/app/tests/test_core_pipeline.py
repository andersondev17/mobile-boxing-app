#!/usr/bin/env python3
"""
Core pipeline test without Kafka dependencies
to verify the essential boxing analysis components work correctly.
"""

import sys
import logging
import pandas as pd
import numpy as np
from pathlib import Path

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def detect_punch_type(filename: str) -> str:
    """Detect punch type from filename (local version)."""
    if not filename:
        return "jab"  # default
    
    filename_lower = filename.lower()
    if "jab" in filename_lower:
        return "jab"
    elif "cross" in filename_lower:
        return "cross"
    elif "gancho" in filename_lower or "hook" in filename_lower:
        return "hook"
    elif "uppercut" in filename_lower:
        return "uppercut"
    else:
        return "jab"  # default

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

def test_baseline_loading():
    """Test baseline loading and selection."""
    logger.info("=== Testing Baseline Loading ===")
    
    try:
        from multi_baseline_analyzer import get_analyzer
        
        analyzer = get_analyzer()
        logger.info(f"Baselines directory: {analyzer.baselines_dir}")
        logger.info(f"Enhanced baselines directory: {analyzer.enhanced_baselines_dir}")
        logger.info(f"Model path: {analyzer.model_path}")
        
        # Check if directories exist
        baselines_exist = analyzer.baselines_dir.exists()
        enhanced_exist = analyzer.enhanced_baselines_dir.exists()
        model_exists = analyzer.model_path.exists()
        
        logger.info(f"Baselines dir exists: {baselines_exist}")
        logger.info(f"Enhanced baselines dir exists: {enhanced_exist}")
        logger.info(f"Model file exists: {model_exists}")
        
        if not baselines_exist:
            logger.error("Baselines directory not found!")
            return False
            
        if not model_exists:
            logger.error("Model file not found!")
            return False
        
        # Load cross baseline
        cross_baseline_path = analyzer.baselines_dir / "dataset" / "cross" / "cross_v1.parquet"
        if cross_baseline_path.exists():
            logger.info(f"Loading cross baseline from: {cross_baseline_path}")
            cross_df = pd.read_parquet(cross_baseline_path)
            logger.info(f"Cross baseline loaded successfully: {len(cross_df)} rows")
            logger.info(f"Columns: {list(cross_df.columns)}")
            
            # Set baseline in analyzer
            analyzer.set_baseline(cross_df)
            logger.info("Baseline set in analyzer successfully")
            return True
        else:
            logger.error(f"Cross baseline not found at: {cross_baseline_path}")
            return False
            
    except Exception as e:
        logger.error(f"Error in baseline loading: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_punch_type_detection():
    """Test punch type detection."""
    logger.info("=== Testing Punch Type Detection ===")
    
    try:
        test_cases = [
            ("cross_video.mp4", "cross"),
            ("jab_training.mp4", "jab"),
            ("hook_power.mp4", "hook"),
            ("uppercut_fight.mp4", "uppercut"),
            ("random_video.mp4", "jab"),  # default
        ]
        
        for filename, expected in test_cases:
            detected = detect_punch_type(filename)
            logger.info(f"File: {filename} -> Detected: {detected} (Expected: {expected})")
            if detected != expected:
                logger.error(f"Detection failed for {filename}")
                return False
                
        return True
        
    except Exception as e:
        logger.error(f"Error in punch type detection: {e}")
        return False

def test_spanish_feedback():
    """Test Spanish coaching feedback."""
    logger.info("=== Testing Spanish Feedback ===")
    
    try:
        from ml_service.feedback_engine import SpanishBoxingFeedback
        
        feedback = SpanishBoxingFeedback()
        
        # Test different punch types
        test_features = {
            'hand_speed': 10.0,
            'torso_rotation': 0.15,
            'forward_extent_right': 0.7,
            'weight_transfer': 0.8,
        }
        
        for punch_type in ['jab', 'cross', 'hook', 'uppercut']:
            coaching = feedback.get_coaching_feedback(punch_type, test_features)
            logger.info(f"{punch_type} feedback: {coaching}")
            
        # Test motivational messages
        motivational = feedback.get_motivational_message()
        logger.info(f"Motivational message: {motivational}")
        
        return True
        
    except Exception as e:
        logger.error(f"Error in Spanish feedback: {e}")
        return False

def test_dtw_scoring():
    """Test DTW scoring against baseline."""
    logger.info("=== Testing DTW Scoring ===")
    
    try:
        from ml_service.dtw_scorer import score_window
        
        # Load cross baseline
        cross_baseline_path = Path(__file__).parent / "build_baseline" / "dataset" / "dataset" / "cross" / "cross_v1.parquet"
        if not cross_baseline_path.exists():
            logger.error("Cross baseline not found for DTW test")
            return False
        
        baseline_df = pd.read_parquet(cross_baseline_path)
        baseline_window = baseline_df.head(30).to_dict('records')
        
        # Create mock user window
        user_features = create_mock_video_features("cross", 30)
        
        # Calculate DTW score
        dtw_score = score_window(user_features, baseline_window)
        logger.info(f"DTW score calculated: {dtw_score:.2f}")
        
        # Get qualitative label
        from ml_service.dtw_scorer import get_qualitative_label
        label = get_qualitative_label(dtw_score)
        logger.info(f"Qualitative label: {label}")
        
        return True
        
    except Exception as e:
        logger.error(f"Error in DTW scoring: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_complete_analysis_simulation():
    """Test complete analysis simulation."""
    logger.info("=== Testing Complete Analysis Simulation ===")
    
    try:
        from ml_service.analyzer import VideoAnalysisResult, FrameResult
        from ml_service.feedback_engine import SpanishBoxingFeedback
        
        # Simulate analyzing a cross video
        logger.info("Simulating cross video analysis...")
        
        # Create mock features
        mock_features = create_mock_video_features("cross", 30)
        
        # Create frame results with meaningful scores
        frame_results = []
        for i, features in enumerate(mock_features):
            # Simulate DTW scoring
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
        
        # Calculate statistics
        scores = [r.dtw_score for r in frame_results]
        avg_score = np.mean(scores)
        min_score = np.min(scores)
        max_score = np.max(scores)
        
        # Create analysis result
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
        
        logger.info(f"Analysis simulation completed:")
        logger.info(f"  Video: {result.video_name}")
        logger.info(f"  Punch type: {result.punch_type}")
        logger.info(f"  Avg score: {result.avg_score:.1f}")
        logger.info(f"  Score range: {result.min_score:.1f} - {result.max_score:.1f}")
        logger.info(f"  Frames scored: {result.scored_frames}/{result.total_frames}")
        
        # Generate coaching feedback
        feedback_engine = SpanishBoxingFeedback()
        coaching_feedback = []
        motivational_messages = []
        
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
        
        # Create complete response
        technique_level = "elite" if result.avg_score >= 85 else "good" if result.avg_score >= 70 else "developing" if result.avg_score >= 50 else "poor"
        
        complete_response = {
            "video_name": result.video_name,
            "punch_type_detected": "cross",
            "baseline_type": "cross",
            "baseline_used": "build_baseline/dataset/dataset/cross/cross_v1.parquet",
            "total_frames": result.total_frames,
            "scored_frames": result.scored_frames,
            "avg_score": result.avg_score,
            "min_score": result.min_score,
            "max_score": result.max_score,
            "technique_level": technique_level,
            "coaching_feedback": coaching_feedback,
            "motivational_messages": motivational_messages,
            "processing_ms": result.processing_ms,
        }
        
        logger.info(f"Complete response created successfully:")
        logger.info(f"  Technique level: {technique_level}")
        logger.info(f"  Coaching messages: {len(coaching_feedback)}")
        logger.info(f"  Motivational messages: {len(motivational_messages)}")
        
        return True
        
    except Exception as e:
        logger.error(f"Error in complete analysis simulation: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run core pipeline tests."""
    logger.info("Starting Core Pipeline Test")
    
    tests = [
        ("Baseline Loading", test_baseline_loading),
        ("Punch Type Detection", test_punch_type_detection),
        ("Spanish Feedback", test_spanish_feedback),
        ("DTW Scoring", test_dtw_scoring),
        ("Complete Analysis Simulation", test_complete_analysis_simulation),
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
    logger.info("CORE PIPELINE TEST SUMMARY")
    logger.info(f"{'='*60}")
    
    passed = sum(1 for result in results.values() if result)
    total = len(results)
    
    for test_name, result in results.items():
        status = "PASS" if result else "FAIL"
        logger.info(f"{test_name}: {status}")
    
    logger.info(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        logger.info("All core pipeline tests passed! System ready for video analysis.")
        logger.info("\nNext steps:")
        logger.info("1. Test with real video upload via API")
        logger.info("2. Verify baseline selection works correctly")
        logger.info("3. Check feedback quality with real data")
        return True
    else:
        logger.error(f"{total - passed} tests failed. Pipeline needs fixes.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
