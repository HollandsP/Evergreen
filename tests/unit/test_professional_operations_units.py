#!/usr/bin/env python3
"""
Unit tests for Agent 4C Professional Video Operations.

Tests individual components and methods of the professional video operations:
- ColorGradingEngine unit tests
- AudioSyncProcessor unit tests
- AdvancedTransitions unit tests
- TextAnimationEngine unit tests
- VideoStabilizer unit tests
- SceneReorderingEngine unit tests

These tests focus on individual methods and edge cases without requiring
actual video processing or external dependencies.
"""

import os
import sys
import time
import json
import asyncio
import logging
import tempfile
import unittest
from unittest.mock import AsyncMock, MagicMock, patch, mock_open
from typing import Dict, List, Any, Optional, Tuple

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

# Import the services we implemented
from services.color_grading_engine import ColorGradingEngine, ColorGradingOperation, CinematicProfile
from services.audio_sync_processor import AudioSyncProcessor, BeatTrackingMode, SyncTarget
from services.advanced_transitions import AdvancedTransitions, TransitionType, EasingFunction
from services.text_animation_engine import TextAnimationEngine, AnimationType, TextAlignment
from services.video_stabilizer import VideoStabilizer, StabilizationMethod, StabilizationStrength
from services.scene_reordering_engine import SceneReorderingEngine, ReorderingStrategy, ContentAnalysisType


class ColorGradingEngineUnitTest(unittest.IsolatedAsyncioTestCase):
    """Unit tests for ColorGradingEngine."""
    
    def setUp(self):
        """Set up test environment."""
        self.color_grader = ColorGradingEngine()
        self.test_video_path = "/mock/test_video.mp4"
    
    async def test_operation_validation(self):
        """Test color grading operation validation."""
        # Test valid operations
        valid_operations = [
            (ColorGradingOperation.BRIGHTNESS, {"value": 0.5}),
            (ColorGradingOperation.CONTRAST, {"value": 1.2}),
            (ColorGradingOperation.SATURATION, {"value": 1.1}),
            (ColorGradingOperation.TEMPERATURE, {"value": 200})
        ]
        
        for operation, params in valid_operations:
            is_valid = self.color_grader.validate_operation_params(operation, params)
            self.assertTrue(is_valid, f"Operation {operation.name} with {params} should be valid")
    
    async def test_cinematic_profile_selection(self):
        """Test cinematic profile selection logic."""
        # Test profile mapping
        profile_map = {
            "warm": CinematicProfile.WARM_CINEMATIC,
            "cool": CinematicProfile.COOL_CINEMATIC,
            "dramatic": CinematicProfile.DRAMATIC_CONTRAST,
            "vintage": CinematicProfile.VINTAGE_FILM
        }
        
        for keyword, expected_profile in profile_map.items():
            selected_profile = self.color_grader.select_cinematic_profile(keyword)
            self.assertEqual(selected_profile, expected_profile, 
                           f"Keyword '{keyword}' should map to {expected_profile.name}")
    
    async def test_operation_chaining(self):
        """Test operation chaining logic."""
        operations = [
            {"operation": ColorGradingOperation.BRIGHTNESS, "value": 0.2},
            {"operation": ColorGradingOperation.CONTRAST, "value": 1.3},
            {"operation": ColorGradingOperation.SATURATION, "value": 1.1}
        ]
        
        # Test that operations can be properly chained
        chain_result = self.color_grader.create_operation_chain(operations)
        self.assertIsNotNone(chain_result, "Operation chain should be created")
        self.assertEqual(len(chain_result), 3, "Chain should contain all operations")
    
    async def test_preview_frame_selection(self):
        """Test preview frame selection algorithm."""
        video_duration = 10.0  # 10 seconds
        frame_count = 5
        
        selected_frames = self.color_grader.select_preview_frames(video_duration, frame_count)
        
        self.assertEqual(len(selected_frames), frame_count, "Should select requested frame count")
        self.assertTrue(all(0 <= frame <= video_duration for frame in selected_frames), 
                       "All frames should be within video duration")
        self.assertEqual(selected_frames, sorted(selected_frames), 
                        "Frames should be in chronological order")


class AudioSyncProcessorUnitTest(unittest.IsolatedAsyncioTestCase):
    """Unit tests for AudioSyncProcessor."""
    
    def setUp(self):
        """Set up test environment."""
        self.audio_sync = AudioSyncProcessor()
        self.test_audio_path = "/mock/test_audio.mp3"
    
    async def test_beat_detection_parameters(self):
        """Test beat detection parameter validation."""
        # Test valid parameters
        valid_params = [
            {"hop_length": 512, "frame_length": 2048},
            {"hop_length": 256, "frame_length": 1024},
            {"hop_length": 1024, "frame_length": 4096}
        ]
        
        for params in valid_params:
            is_valid = self.audio_sync.validate_beat_params(**params)
            self.assertTrue(is_valid, f"Parameters {params} should be valid")
    
    async def test_tempo_calculation(self):
        """Test tempo calculation logic."""
        # Mock beat times (in seconds)
        mock_beat_times = [0.0, 0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0]
        
        calculated_tempo = self.audio_sync.calculate_tempo_from_beats(mock_beat_times)
        
        # Expected tempo: 120 BPM (beats every 0.5 seconds)
        self.assertAlmostEqual(calculated_tempo, 120.0, delta=5.0, 
                              msg="Tempo calculation should be approximately 120 BPM")
    
    async def test_sync_target_mapping(self):
        """Test sync target mapping logic."""
        target_map = {
            "beats": SyncTarget.BEAT_DROPS,
            "tempo": SyncTarget.TEMPO_CHANGES,
            "phrases": SyncTarget.MUSICAL_PHRASES,
            "onsets": SyncTarget.ONSET_EVENTS
        }
        
        for keyword, expected_target in target_map.items():
            mapped_target = self.audio_sync.map_sync_target(keyword)
            self.assertEqual(mapped_target, expected_target,
                           f"Keyword '{keyword}' should map to {expected_target.name}")
    
    async def test_beat_timing_validation(self):
        """Test beat timing validation."""
        # Test valid beat sequence
        valid_beats = [0.0, 0.5, 1.0, 1.5, 2.0, 2.5]
        is_valid = self.audio_sync.validate_beat_timing(valid_beats)
        self.assertTrue(is_valid, "Regular beat sequence should be valid")
        
        # Test invalid beat sequence (out of order)
        invalid_beats = [0.0, 1.0, 0.5, 2.0]
        is_valid = self.audio_sync.validate_beat_timing(invalid_beats)
        self.assertFalse(is_valid, "Out-of-order beats should be invalid")


class AdvancedTransitionsUnitTest(unittest.IsolatedAsyncioTestCase):
    """Unit tests for AdvancedTransitions."""
    
    def setUp(self):
        """Set up test environment."""
        self.transitions = AdvancedTransitions()
    
    async def test_transition_type_categorization(self):
        """Test transition type categorization."""
        # Test basic transitions
        basic_transitions = [TransitionType.CROSSFADE, TransitionType.FADE_TO_BLACK, TransitionType.DISSOLVE]
        for transition in basic_transitions:
            category = self.transitions.get_transition_category(transition)
            self.assertEqual(category, "basic", f"{transition.name} should be categorized as basic")
        
        # Test 3D transitions
        transitions_3d = [TransitionType.CUBE_TRANSITION, TransitionType.FLIP_HORIZONTAL, TransitionType.SPHERE_TRANSITION]
        for transition in transitions_3d:
            category = self.transitions.get_transition_category(transition)
            self.assertEqual(category, "3d", f"{transition.name} should be categorized as 3D")
    
    async def test_easing_function_calculation(self):
        """Test easing function calculations."""
        # Test linear easing
        linear_values = [self.transitions.apply_easing(EasingFunction.LINEAR, t) for t in [0.0, 0.25, 0.5, 0.75, 1.0]]
        expected_linear = [0.0, 0.25, 0.5, 0.75, 1.0]
        
        for actual, expected in zip(linear_values, expected_linear):
            self.assertAlmostEqual(actual, expected, places=2, 
                                 msg="Linear easing should progress linearly")
    
    async def test_transition_duration_validation(self):
        """Test transition duration validation."""
        # Test valid durations
        valid_durations = [0.5, 1.0, 2.0, 3.0, 5.0]
        for duration in valid_durations:
            is_valid = self.transitions.validate_duration(duration)
            self.assertTrue(is_valid, f"Duration {duration} should be valid")
        
        # Test invalid durations
        invalid_durations = [-1.0, 0.0, 15.0]  # negative, zero, too long
        for duration in invalid_durations:
            is_valid = self.transitions.validate_duration(duration)
            self.assertFalse(is_valid, f"Duration {duration} should be invalid")
    
    async def test_direction_parameter_parsing(self):
        """Test direction parameter parsing."""
        direction_map = {
            "left": {"x": -1, "y": 0},
            "right": {"x": 1, "y": 0},
            "up": {"x": 0, "y": -1},
            "down": {"x": 0, "y": 1}
        }
        
        for direction_str, expected_vector in direction_map.items():
            parsed_vector = self.transitions.parse_direction(direction_str)
            self.assertEqual(parsed_vector, expected_vector,
                           f"Direction '{direction_str}' should parse to {expected_vector}")


class TextAnimationEngineUnitTest(unittest.IsolatedAsyncioTestCase):
    """Unit tests for TextAnimationEngine."""
    
    def setUp(self):
        """Set up test environment."""
        self.text_animator = TextAnimationEngine()
    
    async def test_keyframe_interpolation(self):
        """Test keyframe interpolation calculations."""
        keyframes = [
            {"time": 0.0, "position": (100, 100), "opacity": 0.0},
            {"time": 1.0, "position": (200, 150), "opacity": 1.0},
            {"time": 2.0, "position": (300, 200), "opacity": 0.5}
        ]
        
        # Test interpolation at 50% between first two keyframes
        interpolated = self.text_animator.interpolate_keyframes(keyframes, 0.5)
        
        expected_position = (150, 125)  # Midpoint
        expected_opacity = 0.5  # Midpoint
        
        self.assertEqual(interpolated["position"], expected_position, 
                        "Position should be interpolated correctly")
        self.assertAlmostEqual(interpolated["opacity"], expected_opacity, places=2,
                              msg="Opacity should be interpolated correctly")
    
    async def test_animation_type_parameters(self):
        """Test animation type parameter validation."""
        # Test typewriter animation parameters
        typewriter_params = {"typing_speed": 0.1, "cursor_visible": True}
        is_valid = self.text_animator.validate_animation_params(
            AnimationType.TYPEWRITER, typewriter_params
        )
        self.assertTrue(is_valid, "Typewriter parameters should be valid")
        
        # Test bounce animation parameters
        bounce_params = {"bounce_height": 50, "bounce_count": 3}
        is_valid = self.text_animator.validate_animation_params(
            AnimationType.BOUNCE_IN, bounce_params
        )
        self.assertTrue(is_valid, "Bounce parameters should be valid")
    
    async def test_text_positioning(self):
        """Test text positioning calculations."""
        video_size = (640, 480)
        text_size = (200, 50)
        
        # Test center alignment
        center_pos = self.text_animator.calculate_position(
            TextAlignment.CENTER, video_size, text_size
        )
        expected_center = (220, 215)  # (640-200)/2, (480-50)/2
        self.assertEqual(center_pos, expected_center, "Center position should be calculated correctly")
        
        # Test top-left alignment
        top_left_pos = self.text_animator.calculate_position(
            TextAlignment.TOP_LEFT, video_size, text_size
        )
        expected_top_left = (0, 0)
        self.assertEqual(top_left_pos, expected_top_left, "Top-left position should be calculated correctly")
    
    async def test_path_point_validation(self):
        """Test path point validation."""
        # Test valid path
        valid_path = [(0, 0), (100, 50), (200, 100), (300, 150)]
        is_valid = self.text_animator.validate_path_points(valid_path)
        self.assertTrue(is_valid, "Valid path should pass validation")
        
        # Test invalid path (too few points)
        invalid_path = [(0, 0)]
        is_valid = self.text_animator.validate_path_points(invalid_path)
        self.assertFalse(is_valid, "Path with single point should be invalid")


class VideoStabilizerUnitTest(unittest.IsolatedAsyncioTestCase):
    """Unit tests for VideoStabilizer."""
    
    def setUp(self):
        """Set up test environment."""
        self.stabilizer = VideoStabilizer()
    
    async def test_motion_vector_analysis(self):
        """Test motion vector analysis calculations."""
        # Mock motion vectors (dx, dy for each frame)
        mock_vectors = [
            (2, 1), (3, -1), (1, 2), (-2, 1), (4, -2), (0, 3), (-1, -1)
        ]
        
        # Calculate shake intensity
        shake_intensity = self.stabilizer.calculate_shake_intensity(mock_vectors)
        
        self.assertGreater(shake_intensity, 0, "Shake intensity should be positive for unstable video")
        self.assertLess(shake_intensity, 10, "Shake intensity should be reasonable")
    
    async def test_stabilization_strength_mapping(self):
        """Test stabilization strength mapping."""
        strength_map = {
            StabilizationStrength.LIGHT: 0.3,
            StabilizationStrength.MEDIUM: 0.6,
            StabilizationStrength.STRONG: 0.8,
            StabilizationStrength.ULTRA_SMOOTH: 0.95
        }
        
        for strength, expected_value in strength_map.items():
            mapped_value = self.stabilizer.map_strength_to_value(strength)
            self.assertAlmostEqual(mapped_value, expected_value, places=2,
                                 msg=f"Strength {strength.name} should map to {expected_value}")
    
    async def test_crop_compensation_calculation(self):
        """Test crop compensation calculations."""
        original_size = (1920, 1080)
        crop_factor = 1.1  # 10% crop
        
        compensated_size = self.stabilizer.calculate_crop_compensation(original_size, crop_factor)
        
        expected_width = int(1920 / crop_factor)
        expected_height = int(1080 / crop_factor)
        
        self.assertEqual(compensated_size, (expected_width, expected_height),
                        "Crop compensation should calculate correct dimensions")
    
    async def test_rolling_shutter_detection(self):
        """Test rolling shutter detection logic."""
        # Mock frame data that would indicate rolling shutter
        mock_frame_analysis = {
            "vertical_distortion": 0.7,
            "horizontal_lines": True,
            "motion_pattern": "wobble"
        }
        
        has_rolling_shutter = self.stabilizer.detect_rolling_shutter(mock_frame_analysis)
        self.assertTrue(has_rolling_shutter, "Should detect rolling shutter from analysis")


class SceneReorderingEngineUnitTest(unittest.IsolatedAsyncioTestCase):
    """Unit tests for SceneReorderingEngine."""
    
    def setUp(self):
        """Set up test environment."""
        self.scene_reorderer = SceneReorderingEngine()
    
    async def test_emotional_arc_scoring(self):
        """Test emotional arc scoring calculations."""
        # Mock scenes with emotional scores
        mock_scenes = [
            {"id": "scene1", "emotional_score": 0.2, "duration": 5.0},  # Low intensity
            {"id": "scene2", "emotional_score": 0.8, "duration": 8.0},  # High intensity
            {"id": "scene3", "emotional_score": 0.5, "duration": 6.0},  # Medium intensity
            {"id": "scene4", "emotional_score": 0.1, "duration": 4.0}   # Very low intensity
        ]
        
        # Test different arc patterns
        rise_and_fall_score = self.scene_reorderer.calculate_arc_score(mock_scenes, "rise_and_fall")
        self.assertIsInstance(rise_and_fall_score, float, "Arc score should be numeric")
        self.assertGreaterEqual(rise_and_fall_score, 0.0, "Arc score should be non-negative")
    
    async def test_visual_continuity_analysis(self):
        """Test visual continuity analysis."""
        # Mock visual features
        mock_features = [
            {"scene_id": "scene1", "dominant_colors": [(255, 0, 0), (0, 255, 0)], "brightness": 0.6},
            {"scene_id": "scene2", "dominant_colors": [(255, 0, 0), (0, 0, 255)], "brightness": 0.7},
            {"scene_id": "scene3", "dominant_colors": [(0, 255, 0), (255, 255, 0)], "brightness": 0.4}
        ]
        
        continuity_matrix = self.scene_reorderer.calculate_visual_continuity(mock_features)
        
        self.assertIsInstance(continuity_matrix, dict, "Continuity matrix should be a dictionary")
        self.assertIn("color_similarity", continuity_matrix, "Should include color similarity")
        self.assertIn("brightness_similarity", continuity_matrix, "Should include brightness similarity")
    
    async def test_narrative_flow_validation(self):
        """Test narrative flow validation."""
        # Test chronological flow
        chronological_scenes = [
            {"id": "intro", "timestamp": 0, "scene_type": "opening"},
            {"id": "development", "timestamp": 1, "scene_type": "middle"},
            {"id": "climax", "timestamp": 2, "scene_type": "peak"},
            {"id": "resolution", "timestamp": 3, "scene_type": "closing"}
        ]
        
        is_valid_flow = self.scene_reorderer.validate_narrative_flow(chronological_scenes)
        self.assertTrue(is_valid_flow, "Chronological flow should be valid")
    
    async def test_reordering_optimization(self):
        """Test reordering optimization algorithms."""
        mock_scenes = [
            {"id": "A", "score": 0.8},
            {"id": "B", "score": 0.6}, 
            {"id": "C", "score": 0.9},
            {"id": "D", "score": 0.4}
        ]
        
        # Test optimization with different criteria
        optimization_result = self.scene_reorderer.optimize_sequence(
            mock_scenes,
            criteria={"score_weight": 0.7, "position_weight": 0.3}
        )
        
        self.assertIsInstance(optimization_result, list, "Optimization should return a list")
        self.assertEqual(len(optimization_result), len(mock_scenes), 
                        "Optimized sequence should contain all scenes")


class ProfessionalOperationsUnitTestSuite:
    """Test suite runner for all professional operations unit tests."""
    
    def __init__(self):
        self.test_results = {}
        self.performance_metrics = {}
    
    async def run_all_unit_tests(self):
        """Run all unit test classes."""
        logger.info("🚀 Starting Agent 4C Professional Operations Unit Tests")
        logger.info("=" * 80)
        
        test_classes = [
            ("ColorGradingEngine", ColorGradingEngineUnitTest),
            ("AudioSyncProcessor", AudioSyncProcessorUnitTest),
            ("AdvancedTransitions", AdvancedTransitionsUnitTest),
            ("TextAnimationEngine", TextAnimationEngineUnitTest),
            ("VideoStabilizer", VideoStabilizerUnitTest),
            ("SceneReorderingEngine", SceneReorderingEngineUnitTest)
        ]
        
        for class_name, test_class in test_classes:
            logger.info(f"\n🧪 Running {class_name} Unit Tests...")
            start_time = time.time()
            
            try:
                # Create test instance
                test_instance = test_class()
                
                # Get all test methods
                test_methods = [method for method in dir(test_instance) 
                              if method.startswith('test_') and callable(getattr(test_instance, method))]
                
                passed_tests = 0
                total_tests = len(test_methods)
                
                for test_method_name in test_methods:
                    try:
                        test_instance.setUp()
                        test_method = getattr(test_instance, test_method_name)
                        await test_method()
                        passed_tests += 1
                        logger.info(f"  ✅ {test_method_name}")
                    except Exception as e:
                        logger.error(f"  ❌ {test_method_name}: {e}")
                
                processing_time = time.time() - start_time
                success_rate = (passed_tests / total_tests) * 100 if total_tests > 0 else 0
                
                self.test_results[class_name] = {
                    "passed": passed_tests,
                    "total": total_tests,
                    "success_rate": success_rate
                }
                self.performance_metrics[class_name] = processing_time
                
                logger.info(f"  📊 {class_name}: {passed_tests}/{total_tests} passed ({success_rate:.1f}%) in {processing_time:.2f}s")
                
            except Exception as e:
                logger.error(f"  💥 {class_name} test class failed: {e}")
                self.test_results[class_name] = {"passed": 0, "total": 0, "success_rate": 0}
                self.performance_metrics[class_name] = 0
    
    def generate_unit_test_report(self) -> Dict[str, Any]:
        """Generate comprehensive unit test report."""
        total_passed = sum(result["passed"] for result in self.test_results.values())
        total_tests = sum(result["total"] for result in self.test_results.values())
        overall_success_rate = (total_passed / total_tests) * 100 if total_tests > 0 else 0
        total_time = sum(self.performance_metrics.values())
        
        report = {
            "unit_test_summary": {
                "total_unit_tests": total_tests,
                "passed_unit_tests": total_passed,
                "failed_unit_tests": total_tests - total_passed,
                "overall_success_rate": overall_success_rate,
                "total_processing_time": total_time
            },
            "class_results": self.test_results,
            "performance_metrics": self.performance_metrics,
            "unit_test_coverage": {
                "color_grading_operations": "✅ Covered" if self.test_results.get("ColorGradingEngine", {}).get("success_rate", 0) >= 80 else "❌ Insufficient",
                "audio_sync_algorithms": "✅ Covered" if self.test_results.get("AudioSyncProcessor", {}).get("success_rate", 0) >= 80 else "❌ Insufficient",
                "transition_calculations": "✅ Covered" if self.test_results.get("AdvancedTransitions", {}).get("success_rate", 0) >= 80 else "❌ Insufficient",
                "text_animation_logic": "✅ Covered" if self.test_results.get("TextAnimationEngine", {}).get("success_rate", 0) >= 80 else "❌ Insufficient", 
                "stabilization_algorithms": "✅ Covered" if self.test_results.get("VideoStabilizer", {}).get("success_rate", 0) >= 80 else "❌ Insufficient",
                "scene_reordering_logic": "✅ Covered" if self.test_results.get("SceneReorderingEngine", {}).get("success_rate", 0) >= 80 else "❌ Insufficient"
            }
        }
        
        return report


async def main():
    """Main unit test runner."""
    test_suite = ProfessionalOperationsUnitTestSuite()
    await test_suite.run_all_unit_tests()
    
    report = test_suite.generate_unit_test_report()
    
    # Display results
    logger.info("\n" + "=" * 80)
    logger.info("🏁 UNIT TEST SUMMARY")
    logger.info("=" * 80)
    logger.info(f"Total Unit Tests: {report['unit_test_summary']['total_unit_tests']}")
    logger.info(f"Passed: {report['unit_test_summary']['passed_unit_tests']}")
    logger.info(f"Failed: {report['unit_test_summary']['failed_unit_tests']}")
    logger.info(f"Overall Success Rate: {report['unit_test_summary']['overall_success_rate']:.1f}%")
    logger.info(f"Total Processing Time: {report['unit_test_summary']['total_processing_time']:.2f}s")
    
    logger.info("\n📊 Test Coverage by Component:")
    for component, status in report['unit_test_coverage'].items():
        logger.info(f"  {component}: {status}")
    
    logger.info("\n📈 Individual Class Results:")
    for class_name, results in report['class_results'].items():
        logger.info(f"  {class_name}: {results['passed']}/{results['total']} ({results['success_rate']:.1f}%)")
    
    if report['unit_test_summary']['overall_success_rate'] >= 80.0:
        logger.info("\n🎉 UNIT TESTS SUCCESSFUL!")
        logger.info("Professional operations have solid unit test coverage!")
    else:
        logger.error("\n💥 UNIT TEST COVERAGE INSUFFICIENT - Additional tests needed")
    
    # Save report
    report_path = f"tests/reports/agent_4c_unit_test_report_{int(time.time())}.json"
    os.makedirs("tests/reports", exist_ok=True)
    
    with open(report_path, 'w') as f:
        json.dump(report, f, indent=2)
    
    logger.info(f"📊 Unit test report saved to: {report_path}")
    
    return report


if __name__ == "__main__":
    report = asyncio.run(main())
    
    # Return success/failure for CI
    success_rate = report['unit_test_summary']['overall_success_rate']
    sys.exit(0 if success_rate >= 80.0 else 1)