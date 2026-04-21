#!/usr/bin/env python3
"""
Local test script to verify the complete boxing analysis pipeline
without Docker dependencies.
"""

import sys
import logging
import pandas as pd
from pathlib import Path

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_baseline_loading():
    """Test if baselines can be loaded correctly."""
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
            
        # Try to load a cross baseline
        cross_baseline_path = analyzer.baselines_dir / "dataset" / "cross" / "cross_v1.parquet"
        if cross_baseline_path.exists():
            logger.info(f"Loading cross baseline from: {cross_baseline_path}")
            cross_df = pd.read_parquet(cross_baseline_path)
            logger.info(f"Cross baseline loaded successfully: {len(cross_df)} rows")
            logger.info(f"Columns: {list(cross_df.columns)}")
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
    """Test punch type detection from filenames."""
    logger.info("=== Testing Punch Type Detection ===")
    
    try:
        from routes.boxing import detect_punch_type
        
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
    """Test Spanish coaching feedback generation."""
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

def test_video_analysis_mock():
    """Test video analysis with mock data (no MediaPipe)."""
    logger.info("=== Testing Video Analysis (Mock) ===")
    
    try:
        # Create mock video analysis result to test response structure
        from ml_service.analyzer import VideoAnalysisResult, FrameResult
        import time
        
        # Mock frame results
        frame_results = [
            FrameResult(frame_index=i, dtw_score=75.0 + i, qualitative_label="good", 
                       features={'hand_speed': 10.0, 'torso_rotation': 0.2})
            for i in range(10)
        ]
        
        # Mock analysis result
        result = VideoAnalysisResult(
            video_name="test_cross.mp4",
            total_frames=371,
            scored_frames=10,
            avg_score=80.0,
            min_score=75.0,
            max_score=85.0,
            frame_results=frame_results,
            feedback=["¡Buen trabajo! Tu técnica está mejorando."],
            punch_type="cross",
            processing_ms=2500.0,
            baseline_curve=[75.0] * 10
        )
        
        logger.info(f"Mock analysis result created:")
        logger.info(f"  Video: {result.video_name}")
        logger.info(f"  Punch type: {result.punch_type}")
        logger.info(f"  Avg score: {result.avg_score}")
        logger.info(f"  Frames scored: {result.scored_frames}/{result.total_frames}")
        logger.info(f"  Processing time: {result.processing_ms}ms")
        
        return True
        
    except Exception as e:
        logger.error(f"Error in mock video analysis: {e}")
        return False

def main():
    """Run all tests."""
    logger.info("Starting Local Pipeline Test")
    
    tests = [
        ("Baseline Loading", test_baseline_loading),
        ("Punch Type Detection", test_punch_type_detection),
        ("Spanish Feedback", test_spanish_feedback),
        ("Mock Video Analysis", test_video_analysis_mock),
    ]
    
    results = {}
    for test_name, test_func in tests:
        logger.info(f"\n{'='*50}")
        logger.info(f"Running: {test_name}")
        logger.info(f"{'='*50}")
        
        try:
            result = test_func()
            results[test_name] = result
            status = "PASS" if result else "FAIL"
            logger.info(f"{test_name}: {status}")
        except Exception as e:
            logger.error(f"{test_name}: ERROR - {e}")
            results[test_name] = False
    
    # Summary
    logger.info(f"\n{'='*50}")
    logger.info("TEST SUMMARY")
    logger.info(f"{'='*50}")
    
    passed = sum(1 for result in results.values() if result)
    total = len(results)
    
    for test_name, result in results.items():
        status = "PASS" if result else "FAIL"
        logger.info(f"{test_name}: {status}")
    
    logger.info(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        logger.info("All tests passed! Pipeline components working correctly.")
        return True
    else:
        logger.error(f"{total - passed} tests failed. Pipeline needs fixes.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
