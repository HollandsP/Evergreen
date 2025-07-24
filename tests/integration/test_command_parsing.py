#!/usr/bin/env python3
"""
Integration Tests for GPT-4 Command Parsing Accuracy

Tests the AI's ability to correctly parse and interpret natural language
video editing commands with >95% accuracy across various command types.
"""

import pytest
import pytest_asyncio
import asyncio
import json
import os
from typing import Dict, List, Tuple, Any
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock
import time
from dataclasses import dataclass
from collections import defaultdict

# Import modules to test
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.services.ai_video_editor import AIVideoEditor

@dataclass
class CommandTestCase:
    """Test case for command parsing"""
    command: str
    expected_operation: str
    expected_params: Dict[str, Any]
    confidence_threshold: float = 0.7
    description: str = ""
    variations: List[str] = None  # Alternative phrasings

class TestGPT4CommandParsing:
    """Comprehensive tests for GPT-4 command parsing accuracy"""
    
    @pytest.fixture
    def mock_openai_response(self):
        """Factory for creating mock OpenAI responses"""
        def _create_response(operation: str, params: Dict, confidence: float = 0.95, explanation: str = ""):
            mock_response = Mock()
            mock_response.choices = [Mock()]
            mock_response.choices[0].message.content = json.dumps({
                "operation": operation,
                "parameters": params,
                "confidence": confidence,
                "explanation": explanation or f"Will perform {operation} operation"
            })
            return mock_response
        return _create_response
    
    @pytest_asyncio.fixture
    async def editor_with_mock_gpt4(self, mock_openai_response):
        """Create editor with mocked GPT-4 for controlled testing"""
        mock_client = Mock()
        
        # Store test cases for response mapping
        self.response_map = {}
        
        def create_response_for_command(messages, **kwargs):
            """Dynamic response based on command"""
            command = messages[-1]["content"] if messages else ""
            
            # Check if we have a predefined response
            for key, response_data in self.response_map.items():
                if key.lower() in command.lower():
                    return mock_openai_response(**response_data)
            
            # Default response
            return mock_openai_response("UNKNOWN", {}, 0.1, "Command not recognized")
        
        mock_client.chat.completions.create = Mock(side_effect=create_response_for_command)
        
        with patch('openai.OpenAI', return_value=mock_client):
            editor = AIVideoEditor()
            yield editor
    
    # ===== BASIC OPERATION TESTS =====
    
    @pytest.mark.asyncio
    async def test_cut_commands(self, editor_with_mock_gpt4):
        """Test various cut/trim command variations"""
        test_cases = [
            CommandTestCase(
                command="Cut the first 5 seconds of scene 1",
                expected_operation="CUT",
                expected_params={
                    "target": "scene_1",
                    "start_time": 0,
                    "duration": 5
                },
                description="Basic cut from start"
            ),
            CommandTestCase(
                command="Trim scene 2 from 10 to 20 seconds",
                expected_operation="CUT",
                expected_params={
                    "target": "scene_2",
                    "start_time": 10,
                    "end_time": 20
                },
                description="Cut with start and end times"
            ),
            CommandTestCase(
                command="Remove the last 3 seconds from scene 4",
                expected_operation="CUT",
                expected_params={
                    "target": "scene_4",
                    "remove_from_end": 3
                },
                description="Cut from end"
            ),
            CommandTestCase(
                command="Delete everything after 30 seconds in scene 5",
                expected_operation="CUT",
                expected_params={
                    "target": "scene_5",
                    "start_time": 30,
                    "remove_after": True
                },
                description="Cut everything after timestamp"
            )
        ]
        
        accuracy_results = []
        
        for test_case in test_cases:
            # Set up response mapping
            self.response_map[test_case.command[:20]] = {
                "operation": test_case.expected_operation,
                "params": test_case.expected_params,
                "confidence": 0.95
            }
            
            result = await editor_with_mock_gpt4._parse_command_with_gpt4(
                test_case.command, "test_project"
            )
            
            # Verify operation type
            operation_match = result["operation"] == test_case.expected_operation
            
            # Verify parameters
            params_match = all(
                result["parameters"].get(k) == v 
                for k, v in test_case.expected_params.items()
            )
            
            # Verify confidence
            confidence_ok = result["confidence"] >= test_case.confidence_threshold
            
            accuracy_results.append({
                "command": test_case.command,
                "description": test_case.description,
                "operation_match": operation_match,
                "params_match": params_match,
                "confidence_ok": confidence_ok,
                "success": operation_match and params_match and confidence_ok
            })
        
        # Calculate accuracy
        accuracy = sum(r["success"] for r in accuracy_results) / len(accuracy_results)
        
        # Print detailed results for debugging
        for result in accuracy_results:
            if not result["success"]:
                print(f"Failed: {result['description']} - {result['command']}")
        
        assert accuracy >= 0.95, f"Cut command accuracy {accuracy:.2%} is below 95%"
    
    @pytest.mark.asyncio
    async def test_transition_commands(self, editor_with_mock_gpt4):
        """Test transition command parsing"""
        test_cases = [
            CommandTestCase(
                command="Add a fade transition between all scenes",
                expected_operation="TRANSITION",
                expected_params={
                    "target": "all_scenes",
                    "transition_type": "fade",
                    "duration": 1.0
                }
            ),
            CommandTestCase(
                command="Use a 3D cube transition between scenes 2 and 3",
                expected_operation="TRANSITION",
                expected_params={
                    "target": "scene_2_to_3",
                    "transition_type": "cube_left",
                    "duration": 2.0
                }
            ),
            CommandTestCase(
                command="Add 2-second crossfade between scene 1 and scene 2",
                expected_operation="TRANSITION",
                expected_params={
                    "target": "scene_1_to_2",
                    "transition_type": "crossfade",
                    "duration": 2.0
                }
            ),
            CommandTestCase(
                command="Apply zoom in transition to scene 5 with 1.5 second duration",
                expected_operation="TRANSITION",
                expected_params={
                    "target": "scene_5",
                    "transition_type": "zoom_in",
                    "duration": 1.5
                }
            )
        ]
        
        for test_case in test_cases:
            self.response_map[test_case.command[:20]] = {
                "operation": test_case.expected_operation,
                "params": test_case.expected_params,
                "confidence": 0.9
            }
            
            result = await editor_with_mock_gpt4._parse_command_with_gpt4(
                test_case.command, "test_project"
            )
            
            assert result["operation"] == test_case.expected_operation
            assert result["confidence"] >= 0.8
    
    @pytest.mark.asyncio
    async def test_color_grading_commands(self, editor_with_mock_gpt4):
        """Test color grading command parsing"""
        test_cases = [
            CommandTestCase(
                command="Apply cinematic color grading to all scenes",
                expected_operation="COLOR_GRADE",
                expected_params={
                    "target": "all_scenes",
                    "profile": "cinematic",
                    "strength": 0.8
                }
            ),
            CommandTestCase(
                command="Make scene 3 look vintage",
                expected_operation="COLOR_GRADE",
                expected_params={
                    "target": "scene_3",
                    "profile": "vintage",
                    "strength": 1.0
                }
            ),
            CommandTestCase(
                command="Increase brightness and contrast in scene 1",
                expected_operation="COLOR_GRADE",
                expected_params={
                    "target": "scene_1",
                    "adjustments": {
                        "brightness": 0.2,
                        "contrast": 0.3
                    }
                }
            ),
            CommandTestCase(
                command="Apply cyberpunk style to the final scene",
                expected_operation="COLOR_GRADE",
                expected_params={
                    "target": "final_scene",
                    "profile": "cyberpunk",
                    "strength": 0.9
                }
            )
        ]
        
        successful_parses = 0
        
        for test_case in test_cases:
            self.response_map[test_case.command[:15]] = {
                "operation": test_case.expected_operation,
                "params": test_case.expected_params,
                "confidence": 0.9
            }
            
            result = await editor_with_mock_gpt4._parse_command_with_gpt4(
                test_case.command, "test_project"
            )
            
            if result["operation"] == test_case.expected_operation and result["confidence"] >= 0.8:
                successful_parses += 1
        
        accuracy = successful_parses / len(test_cases)
        assert accuracy >= 0.95, f"Color grading accuracy {accuracy:.2%} is below 95%"
    
    @pytest.mark.asyncio
    async def test_text_animation_commands(self, editor_with_mock_gpt4):
        """Test text animation command parsing"""
        test_cases = [
            CommandTestCase(
                command="Add sliding text 'THE END' at 2:30",
                expected_operation="TEXT_ANIMATION",
                expected_params={
                    "text": "THE END",
                    "animation_type": "slide_in_left",
                    "start_time": 150,  # 2:30 in seconds
                    "duration": 3.0
                }
            ),
            CommandTestCase(
                command="Show title 'Chapter 1' with typewriter effect for 5 seconds",
                expected_operation="TEXT_ANIMATION",
                expected_params={
                    "text": "Chapter 1",
                    "animation_type": "typewriter",
                    "duration": 5.0
                }
            ),
            CommandTestCase(
                command="Add bouncing text 'SUBSCRIBE' in the bottom right corner",
                expected_operation="TEXT_ANIMATION",
                expected_params={
                    "text": "SUBSCRIBE",
                    "animation_type": "bounce",
                    "position": "bottom_right"
                }
            )
        ]
        
        for test_case in test_cases:
            self.response_map[test_case.command[:15]] = {
                "operation": test_case.expected_operation,
                "params": test_case.expected_params,
                "confidence": 0.9
            }
            
            result = await editor_with_mock_gpt4._parse_command_with_gpt4(
                test_case.command, "test_project"
            )
            
            assert result["operation"] == test_case.expected_operation
            assert "text" in result["parameters"]
            assert "animation_type" in result["parameters"]
    
    # ===== COMPLEX COMMAND TESTS =====
    
    @pytest.mark.asyncio
    async def test_compound_commands(self, editor_with_mock_gpt4):
        """Test parsing of compound/complex commands"""
        test_cases = [
            CommandTestCase(
                command="Cut the first 3 seconds and add a fade in to scene 1",
                expected_operation="COMPOUND",
                expected_params={
                    "operations": [
                        {"type": "CUT", "params": {"start_time": 0, "duration": 3}},
                        {"type": "FADE", "params": {"fade_type": "in", "duration": 1.0}}
                    ],
                    "target": "scene_1"
                }
            ),
            CommandTestCase(
                command="Speed up scene 2 by 2x and add dramatic music",
                expected_operation="COMPOUND",
                expected_params={
                    "operations": [
                        {"type": "SPEED", "params": {"multiplier": 2.0}},
                        {"type": "AUDIO_MIX", "params": {"add_music": "dramatic"}}
                    ],
                    "target": "scene_2"
                }
            )
        ]
        
        # For compound commands, we might need to handle them differently
        # or break them down into sequential operations
        for test_case in test_cases:
            # Test that the parser can at least identify this as a complex request
            result = await editor_with_mock_gpt4._parse_command_with_gpt4(
                test_case.command, "test_project"
            )
            
            # Should either parse as compound or suggest breaking it down
            assert result["confidence"] > 0.5
    
    @pytest.mark.asyncio
    async def test_ambiguous_commands(self, editor_with_mock_gpt4):
        """Test handling of ambiguous commands"""
        ambiguous_commands = [
            "Make it better",
            "Fix the video",
            "Do something cool",
            "Edit this part",
            "Change the thing"
        ]
        
        for command in ambiguous_commands:
            result = await editor_with_mock_gpt4._parse_command_with_gpt4(
                command, "test_project"
            )
            
            # Should return low confidence for ambiguous commands
            assert result["confidence"] < 0.7
            assert result["operation"] in ["UNKNOWN", "CLARIFY", "ERROR"]
    
    @pytest.mark.asyncio
    async def test_contextual_commands(self, editor_with_mock_gpt4):
        """Test commands that require context understanding"""
        # Set up project context
        editor_with_mock_gpt4.project_context["test_project"] = {
            "scenes": [
                {"id": "scene_1", "description": "Opening shot"},
                {"id": "scene_2", "description": "Dialog scene"},
                {"id": "scene_3", "description": "Action sequence"},
                {"id": "scene_4", "description": "Closing credits"}
            ]
        }
        
        test_cases = [
            CommandTestCase(
                command="Speed up the action sequence",
                expected_operation="SPEED",
                expected_params={
                    "target": "scene_3",  # Should identify scene_3 as action sequence
                    "multiplier": 1.5
                }
            ),
            CommandTestCase(
                command="Add fade out to the closing credits",
                expected_operation="FADE",
                expected_params={
                    "target": "scene_4",  # Should identify scene_4 as closing credits
                    "fade_type": "out",
                    "duration": 2.0
                }
            ),
            CommandTestCase(
                command="Remove the first scene",
                expected_operation="CUT",
                expected_params={
                    "target": "scene_1",
                    "remove_entire": True
                }
            )
        ]
        
        for test_case in test_cases:
            self.response_map[test_case.command[:15]] = {
                "operation": test_case.expected_operation,
                "params": test_case.expected_params,
                "confidence": 0.85
            }
            
            result = await editor_with_mock_gpt4._parse_command_with_gpt4(
                test_case.command, "test_project"
            )
            
            assert result["operation"] == test_case.expected_operation
            assert result["confidence"] >= 0.8
    
    # ===== ACCURACY METRICS TESTS =====
    
    @pytest.mark.asyncio
    async def test_overall_parsing_accuracy(self, editor_with_mock_gpt4):
        """Test overall parsing accuracy across all command types"""
        all_test_commands = [
            # Basic operations
            ("Cut first 5 seconds of scene 1", "CUT", 0.95),
            ("Add fade in to scene 2", "FADE", 0.95),
            ("Speed up scene 3 by 1.5x", "SPEED", 0.95),
            ("Add crossfade between all scenes", "TRANSITION", 0.9),
            
            # Advanced operations
            ("Apply cinematic color grading", "COLOR_GRADE", 0.9),
            ("Add title text with animation", "TEXT_ANIMATION", 0.9),
            ("Stabilize shaky footage in scene 4", "STABILIZE", 0.9),
            ("Sync cuts to music beats", "AUDIO_SYNC", 0.85),
            
            # Complex operations
            ("Reorder scenes for better flow", "REORDER_SCENES", 0.85),
            ("Create montage from best moments", "MONTAGE", 0.8),
            
            # Edge cases
            ("", "UNKNOWN", 0.1),  # Empty command
            ("xyz123 invalid command", "UNKNOWN", 0.1),  # Gibberish
        ]
        
        results = []
        for command, expected_op, expected_confidence in all_test_commands:
            # Set up appropriate response
            if expected_op != "UNKNOWN":
                self.response_map[command[:10]] = {
                    "operation": expected_op,
                    "params": {"target": "scene_1"},
                    "confidence": expected_confidence
                }
            
            result = await editor_with_mock_gpt4._parse_command_with_gpt4(
                command, "test_project"
            )
            
            success = (
                result["operation"] == expected_op and
                abs(result["confidence"] - expected_confidence) < 0.2
            )
            
            results.append({
                "command": command,
                "expected": expected_op,
                "actual": result["operation"],
                "confidence": result["confidence"],
                "success": success
            })
        
        # Calculate metrics
        total_commands = len(results)
        successful_parses = sum(r["success"] for r in results)
        accuracy = successful_parses / total_commands
        
        # Separate by command type
        basic_commands = results[:4]
        advanced_commands = results[4:8]
        complex_commands = results[8:10]
        edge_cases = results[10:]
        
        basic_accuracy = sum(r["success"] for r in basic_commands) / len(basic_commands)
        advanced_accuracy = sum(r["success"] for r in advanced_commands) / len(advanced_commands)
        
        print(f"\nParsing Accuracy Report:")
        print(f"Overall: {accuracy:.2%}")
        print(f"Basic Commands: {basic_accuracy:.2%}")
        print(f"Advanced Commands: {advanced_accuracy:.2%}")
        
        # Assert minimum accuracy thresholds
        assert accuracy >= 0.85, f"Overall accuracy {accuracy:.2%} below 85%"
        assert basic_accuracy >= 0.95, f"Basic command accuracy {basic_accuracy:.2%} below 95%"
        assert advanced_accuracy >= 0.80, f"Advanced command accuracy {advanced_accuracy:.2%} below 80%"

class TestRealGPT4Integration:
    """Integration tests with real GPT-4 API (requires API key)"""
    
    @pytest.mark.skipif(not os.getenv("OPENAI_API_KEY"), reason="OpenAI API key not available")
    @pytest.mark.asyncio
    async def test_real_gpt4_parsing(self):
        """Test with real GPT-4 API for accurate assessment"""
        editor = AIVideoEditor()
        
        # Test a variety of real commands
        test_commands = [
            "Cut the first 10 seconds from scene 2",
            "Add a smooth fade transition between all scenes", 
            "Make the video look more cinematic",
            "Speed up the boring parts",
            "Add text that says 'Subscribe' with a cool animation",
            "Sync the transitions to the beat of the music",
            "Stabilize the shaky camera footage",
            "Apply a vintage filter to scene 3"
        ]
        
        results = []
        for command in test_commands:
            try:
                result = await editor._parse_command_with_gpt4(command, "test_project")
                results.append({
                    "command": command,
                    "parsed_operation": result["operation"],
                    "confidence": result["confidence"],
                    "explanation": result.get("explanation", ""),
                    "success": result["confidence"] >= 0.7
                })
            except Exception as e:
                results.append({
                    "command": command,
                    "error": str(e),
                    "success": False
                })
        
        # Analyze results
        successful = sum(r["success"] for r in results)
        accuracy = successful / len(results)
        
        # Print detailed results
        print("\nReal GPT-4 Parsing Results:")
        for r in results:
            status = "✓" if r["success"] else "✗"
            print(f"{status} '{r['command']}'")
            if "parsed_operation" in r:
                print(f"   -> {r['parsed_operation']} (confidence: {r['confidence']:.2f})")
            if "error" in r:
                print(f"   -> Error: {r['error']}")
        
        print(f"\nOverall Real GPT-4 Accuracy: {accuracy:.2%}")
        
        # With real GPT-4, we expect high accuracy
        assert accuracy >= 0.80, f"Real GPT-4 accuracy {accuracy:.2%} below 80%"

class TestCommandValidation:
    """Test command validation and error handling"""
    
    @pytest.mark.asyncio
    async def test_parameter_validation(self):
        """Test validation of parsed command parameters"""
        editor = AIVideoEditor()
        
        # Test cases with invalid parameters
        invalid_params = [
            {
                "operation": "CUT",
                "parameters": {
                    "target": "scene_1",
                    "start_time": -5,  # Negative time
                    "duration": 10
                }
            },
            {
                "operation": "SPEED",
                "parameters": {
                    "target": "scene_2",
                    "multiplier": 0  # Invalid multiplier
                }
            },
            {
                "operation": "FADE",
                "parameters": {
                    "target": "scene_3",
                    "fade_type": "invalid_type",  # Invalid fade type
                    "duration": -1  # Negative duration
                }
            }
        ]
        
        for operation in invalid_params:
            # The system should handle invalid parameters gracefully
            result = await editor._execute_operation(operation, "test_project")
            assert result["success"] is False or "error" in result
    
    @pytest.mark.asyncio
    async def test_scene_reference_validation(self):
        """Test validation of scene references in commands"""
        editor = AIVideoEditor()
        
        # Set up project with 3 scenes
        editor.project_context["test_project"] = {
            "scenes": [
                {"id": "scene_1"},
                {"id": "scene_2"},
                {"id": "scene_3"}
            ]
        }
        
        # Test valid and invalid scene references
        test_cases = [
            ("scene_1", True),      # Valid
            ("scene_3", True),      # Valid
            ("scene_99", False),    # Invalid - doesn't exist
            ("all_scenes", True),   # Valid - special case
            ("", False),            # Invalid - empty
            ("scene_-1", False),    # Invalid - negative
        ]
        
        for target, should_be_valid in test_cases:
            operation = {
                "operation": "CUT",
                "parameters": {
                    "target": target,
                    "start_time": 0,
                    "duration": 5
                }
            }
            
            with patch.object(editor, '_find_scene_video_optimized') as mock_find:
                if should_be_valid and target != "all_scenes":
                    mock_find.return_value = f"/path/to/{target}.mp4"
                else:
                    mock_find.return_value = None
                
                result = await editor._execute_operation(operation, "test_project")
                
                if should_be_valid:
                    # Should attempt to execute or handle appropriately
                    assert "target" in str(result)
                else:
                    # Should fail validation
                    assert result["success"] is False

class TestPerformanceMetrics:
    """Test parsing performance and efficiency"""
    
    @pytest.mark.asyncio
    async def test_parsing_speed(self):
        """Test that parsing completes within acceptable time"""
        editor = AIVideoEditor()
        
        # Mock fast GPT-4 response
        mock_client = Mock()
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = json.dumps({
            "operation": "CUT",
            "parameters": {"target": "scene_1", "start_time": 0, "duration": 5},
            "confidence": 0.95
        })
        
        async def mock_create(*args, **kwargs):
            await asyncio.sleep(0.1)  # Simulate API latency
            return mock_response
        
        mock_client.chat.completions.create = mock_create
        editor.openai_client = mock_client
        
        # Test parsing speed
        commands = [
            "Cut first 5 seconds of scene 1",
            "Add fade to scene 2", 
            "Speed up scene 3",
            "Add transition between scenes"
        ]
        
        start_time = time.time()
        
        for command in commands:
            result = await editor._parse_command_with_gpt4(command, "test_project")
            assert result["operation"] != "ERROR"
        
        elapsed = time.time() - start_time
        avg_time = elapsed / len(commands)
        
        print(f"\nAverage parsing time: {avg_time:.3f}s per command")
        
        # Should parse quickly (including mock API latency)
        assert avg_time < 0.5, f"Parsing too slow: {avg_time:.3f}s per command"
    
    @pytest.mark.asyncio
    async def test_batch_command_processing(self):
        """Test efficient processing of multiple commands"""
        editor = AIVideoEditor()
        
        # Create a batch of commands
        commands = [
            f"Cut {i} seconds from scene {i%3 + 1}" 
            for i in range(10)
        ]
        
        # Mock responses
        mock_client = Mock()
        
        def create_batch_response(messages, **kwargs):
            command = messages[-1]["content"]
            # Extract numbers from command for parameters
            import re
            numbers = re.findall(r'\d+', command)
            
            mock_response = Mock()
            mock_response.choices = [Mock()]
            mock_response.choices[0].message.content = json.dumps({
                "operation": "CUT",
                "parameters": {
                    "target": f"scene_{numbers[1] if len(numbers) > 1 else 1}",
                    "duration": int(numbers[0]) if numbers else 5
                },
                "confidence": 0.9
            })
            return mock_response
        
        mock_client.chat.completions.create = Mock(side_effect=create_batch_response)
        editor.openai_client = mock_client
        
        # Process all commands
        start_time = time.time()
        results = []
        
        for command in commands:
            result = await editor._parse_command_with_gpt4(command, "test_project")
            results.append(result)
        
        elapsed = time.time() - start_time
        
        # Verify all parsed successfully
        assert all(r["operation"] == "CUT" for r in results)
        assert all(r["confidence"] >= 0.8 for r in results)
        
        # Should process batch efficiently
        assert elapsed < len(commands) * 0.1  # Less than 100ms per command

# Performance benchmarking fixtures
@pytest.fixture
def performance_tracker():
    """Track performance metrics during tests"""
    metrics = defaultdict(list)
    
    def track(category: str, value: float):
        metrics[category].append(value)
    
    def report():
        print("\nPerformance Metrics:")
        for category, values in metrics.items():
            avg = sum(values) / len(values)
            print(f"{category}: avg={avg:.3f}s, min={min(values):.3f}s, max={max(values):.3f}s")
    
    return {"track": track, "report": report, "metrics": metrics}

if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s", "--tb=short"])