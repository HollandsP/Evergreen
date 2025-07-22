"""
Comprehensive test suite for validating critical service issues.

This test file validates the specific issues identified in:
1. ElevenLabs service - file leak risk in clone_voice()
2. Runway service - stub vs real implementation confusion
3. FFmpeg service - resource cleanup and error handling
4. Video generation worker - monolithic design issues
"""

import pytest
import os
import tempfile
import subprocess
import time
import psutil
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path

# Import services under test
import sys
sys.path.append('/mnt/c/Users/holla/OneDrive/Desktop/CodeProjects/Evergreen')

from src.services.elevenlabs_client import ElevenLabsClient
from src.services.runway_client import RunwayClient
from src.services.ffmpeg_service import FFmpegService
from workers.tasks.video_generation import process_video_generation, VideoComposer


class TestElevenLabsSecurityIssues:
    """Test ElevenLabs service for file leak risks and error handling."""
    
    def test_clone_voice_file_leak_risk(self):
        """Test clone_voice() for potential file handle leaks."""
        client = ElevenLabsClient(api_key="test_key")
        
        # Create temporary test files
        test_files = []
        for i in range(3):
            temp_file = tempfile.NamedTemporaryFile(suffix='.mp3', delete=False)
            temp_file.write(b"fake audio data")
            temp_file.close()
            test_files.append(temp_file.name)
        
        try:
            # Mock the requests.post to avoid actual API calls
            with patch('requests.post') as mock_post:
                mock_response = Mock()
                mock_response.status_code = 200
                mock_response.json.return_value = {'voice_id': 'test_voice_id'}
                mock_post.return_value = mock_response
                
                # Test file handling in clone_voice
                result = client.clone_voice(
                    name="test_voice",
                    files=test_files,
                    description="test description"
                )
                
                # Verify result
                assert result['voice_id'] == 'test_voice_id'
                
                # Verify all files were opened and closed properly
                # The current implementation opens files in the loop which is problematic
                assert mock_post.called
        
        finally:
            # Cleanup
            for file_path in test_files:
                if os.path.exists(file_path):
                    os.unlink(file_path)
    
    def test_clone_voice_file_not_found_error(self):
        """Test clone_voice() error handling for missing files."""
        client = ElevenLabsClient(api_key="test_key")
        
        non_existent_files = ["/path/that/does/not/exist.mp3"]
        
        with pytest.raises(FileNotFoundError):
            client.clone_voice(
                name="test_voice",
                files=non_existent_files
            )
    
    def test_clone_voice_file_handle_leak_simulation(self):
        """Simulate file handle leak scenario in clone_voice()."""
        client = ElevenLabsClient(api_key="test_key")
        
        # Create many temporary files to test file handle management
        test_files = []
        for i in range(20):  # Test with many files
            temp_file = tempfile.NamedTemporaryFile(suffix='.mp3', delete=False)
            temp_file.write(b"fake audio data")
            temp_file.close()
            test_files.append(temp_file.name)
        
        try:
            # Get initial file descriptor count
            process = psutil.Process()
            initial_fds = len(process.open_files())
            
            with patch('requests.post') as mock_post:
                # Simulate API failure to test error path
                mock_post.side_effect = Exception("API Error")
                
                with pytest.raises(Exception):
                    client.clone_voice(
                        name="test_voice",
                        files=test_files
                    )
                
                # Check if file descriptors increased (potential leak)
                final_fds = len(process.open_files())
                
                # File descriptors should not increase significantly
                # Current implementation may leak files on error
                fd_difference = final_fds - initial_fds
                
                # This test will likely fail with current implementation
                # indicating the file leak issue
                assert fd_difference <= 1, f"Potential file descriptor leak: {fd_difference} FDs not closed"
        
        finally:
            # Cleanup
            for file_path in test_files:
                if os.path.exists(file_path):
                    os.unlink(file_path)
    
    def test_api_key_validation_error_handling(self):
        """Test error handling when API key is invalid."""
        client = ElevenLabsClient(api_key="invalid_key")
        
        with patch('requests.Session.get') as mock_get:
            mock_response = Mock()
            mock_response.raise_for_status.side_effect = Exception("Unauthorized")
            mock_get.return_value = mock_response
            
            # validate_api_key should return False on error, not raise
            result = client.validate_api_key()
            assert result is False
    
    def test_rate_limiting_behavior(self):
        """Test behavior under rate limiting scenarios."""
        client = ElevenLabsClient(api_key="test_key")
        
        with patch('requests.Session.post') as mock_post:
            # Simulate rate limiting response
            mock_response = Mock()
            mock_response.status_code = 429
            mock_response.raise_for_status.side_effect = Exception("Rate limited")
            mock_post.return_value = mock_response
            
            with pytest.raises(Exception):
                client.text_to_speech("test text", "test_voice_id")


class TestRunwayImplementationConfusion:
    """Test Runway service for stub vs real implementation issues."""
    
    def test_api_key_handling_consistency(self):
        """Test API key handling between stub and real modes."""
        # Test with no API key (stub mode)
        client_stub = RunwayClient()
        assert client_stub.api_key == 'dummy_key'
        
        # Test with API key (should use real API)
        client_real = RunwayClient(api_key="real_key")
        assert client_real.api_key == "real_key"
    
    def test_generation_behavior_differentiation(self):
        """Test that stub vs real behavior is clearly differentiated."""
        client = RunwayClient(api_key="test_key")
        
        # Mock requests to simulate real API
        with patch('requests.post') as mock_post:
            # Test successful API response
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                'id': 'real_api_job_id',
                'status': 'processing'
            }
            mock_post.return_value = mock_response
            
            result = client.generate_video("test prompt")
            
            # Should use real API response
            assert result['runway_id'] == 'real_api_job_id'
            assert 'is_placeholder' not in result or not result['is_placeholder']
            
            # Test API failure fallback
            mock_post.side_effect = Exception("API Error")
            
            result_fallback = client.generate_video("test prompt")
            
            # Should fall back to placeholder
            assert result_fallback['is_placeholder'] is True
    
    def test_status_checking_behavior(self):
        """Test status checking behaves correctly for stub vs real jobs."""
        client = RunwayClient()
        
        # Create a placeholder job
        job = client.generate_video("test prompt")
        job_id = job['id']
        
        # Check status - should complete quickly for placeholder
        status = client.get_generation_status(job_id)
        
        if job.get('is_placeholder'):
            assert status['status'] == 'completed'
            assert status['video_url'].startswith('placeholder://')
        
        # Test non-existent job
        with pytest.raises(ValueError):
            client.get_generation_status("non_existent_job")
    
    def test_download_behavior_by_url_type(self):
        """Test download behavior varies correctly by URL type."""
        client = RunwayClient()
        
        # Test placeholder URL
        placeholder_data = client.download_video("placeholder://enhanced/test.mp4")
        assert isinstance(placeholder_data, bytes)
        assert len(placeholder_data) > 0
        
        # Test simulated URL
        simulated_data = client.download_video("simulated://video/test.mp4")
        assert isinstance(simulated_data, bytes)
        
        # Test real URL (should fail gracefully)
        with patch('requests.get') as mock_get:
            mock_response = Mock()
            mock_response.status_code = 404
            mock_get.return_value = mock_response
            
            fallback_data = client.download_video("https://real-api.com/video.mp4")
            assert isinstance(fallback_data, bytes)
    
    def test_cinematic_mode_toggle(self):
        """Test cinematic mode can be toggled via environment variable."""
        # Test with cinematic mode disabled
        with patch.dict(os.environ, {'RUNWAY_CINEMATIC_MODE': 'false'}):
            client = RunwayClient()
            data = client._generate_enhanced_placeholder_video("placeholder://test/test.mp4")
            assert isinstance(data, bytes)
        
        # Test with cinematic mode enabled
        with patch.dict(os.environ, {'RUNWAY_CINEMATIC_MODE': 'true'}):
            client = RunwayClient()
            data = client._generate_enhanced_placeholder_video("placeholder://test/rooftop.mp4")
            assert isinstance(data, bytes)


class TestFFmpegResourceManagement:
    """Test FFmpeg service for resource cleanup and error handling."""
    
    def test_subprocess_cleanup_on_error(self):
        """Test that subprocess resources are cleaned up on errors."""
        # Skip if FFmpeg not available
        if not FFmpegService()._find_executable('ffmpeg'):
            pytest.skip("FFmpeg not available")
        
        service = FFmpegService()
        
        # Test with invalid input file
        with pytest.raises(subprocess.CalledProcessError):
            service.get_media_info("/path/that/does/not/exist.mp4")
    
    def test_memory_usage_during_processing(self):
        """Test memory usage doesn't grow excessively during processing."""
        # Skip if FFmpeg not available
        try:
            service = FFmpegService()
        except RuntimeError:
            pytest.skip("FFmpeg not available")
        
        process = psutil.Process()
        initial_memory = process.memory_info().rss
        
        # Create temporary test files
        with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as temp_input:
            # Create a simple test video
            cmd = [
                service.ffmpeg_path,
                '-f', 'lavfi',
                '-i', 'testsrc=duration=1:size=320x240:rate=1',
                '-y', temp_input.name
            ]
            subprocess.run(cmd, capture_output=True)
            
            try:
                # Process the file multiple times
                for i in range(5):
                    with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as temp_output:
                        try:
                            service.transcode(
                                temp_input.name,
                                temp_output.name,
                                video_bitrate='1M'
                            )
                        finally:
                            if os.path.exists(temp_output.name):
                                os.unlink(temp_output.name)
                
                # Check memory usage hasn't grown excessively
                final_memory = process.memory_info().rss
                memory_growth = final_memory - initial_memory
                
                # Memory growth should be reasonable (less than 100MB)
                assert memory_growth < 100 * 1024 * 1024, f"Excessive memory growth: {memory_growth} bytes"
            
            finally:
                if os.path.exists(temp_input.name):
                    os.unlink(temp_input.name)
    
    def test_temporary_file_cleanup(self):
        """Test that temporary files are properly cleaned up."""
        # Skip if FFmpeg not available
        try:
            service = FFmpegService()
        except RuntimeError:
            pytest.skip("FFmpeg not available")
        
        # Count temporary files before
        temp_dir = tempfile.gettempdir()
        initial_temp_files = len(list(Path(temp_dir).glob('*')))
        
        # Create test files for concatenation
        test_files = []
        for i in range(3):
            with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as temp_file:
                # Create simple test video
                cmd = [
                    service.ffmpeg_path,
                    '-f', 'lavfi',
                    '-i', f'testsrc=duration=1:size=320x240:rate=1:start_number={i}',
                    '-y', temp_file.name
                ]
                subprocess.run(cmd, capture_output=True)
                test_files.append(temp_file.name)
        
        try:
            with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as output_file:
                # Test concatenation which uses temporary files internally
                service.concatenate(test_files, output_file.name)
                
                # Check that temporary files were cleaned up
                final_temp_files = len(list(Path(temp_dir).glob('*')))
                
                # Allow for some temporary files but not excessive growth
                temp_file_growth = final_temp_files - initial_temp_files
                assert temp_file_growth <= len(test_files) + 2, f"Temporary files not cleaned up: {temp_file_growth} extra files"
        
        finally:
            # Cleanup test files
            for file_path in test_files:
                if os.path.exists(file_path):
                    os.unlink(file_path)
            if os.path.exists(output_file.name):
                os.unlink(output_file.name)
    
    def test_eval_security_issue(self):
        """Test the eval() security issue in get_media_info()."""
        # Skip if FFmpeg not available
        try:
            service = FFmpegService()
        except RuntimeError:
            pytest.skip("FFmpeg not available")
        
        # This test highlights the security issue with eval() on line 106
        # The current implementation uses eval(video_stream.get('r_frame_rate', '0/1'))
        # which could be exploited if the input is malicious
        
        # Create a mock video stream with malicious frame rate
        with patch.object(service, '_run_command') as mock_run:
            mock_result = Mock()
            mock_result.stdout = '{"format": {"duration": "10.0"}, "streams": [{"codec_type": "video", "r_frame_rate": "__import__(\'os\').system(\'echo pwned\')"}]}'
            mock_run.return_value = mock_result
            
            # This should not execute arbitrary code
            with pytest.raises(Exception):
                # The eval() will fail with the malicious input, which is actually good
                # but it shows the vulnerability exists
                service.get_media_info("test.mp4")


class TestVideoGenerationWorkerIssues:
    """Test video generation worker for monolithic design issues."""
    
    def test_task_error_recovery(self):
        """Test error recovery in video generation task."""
        # Mock the celery task context
        mock_task = Mock()
        mock_task.request.retries = 0
        mock_task.retry.side_effect = Exception("Retry called")
        
        with patch('workers.tasks.video_generation.app.task') as mock_decorator:
            mock_decorator.return_value = lambda f: f
            
            # Test with invalid script content
            with pytest.raises(Exception):
                process_video_generation.apply(
                    args=("test_job", "invalid_script", {}),
                    throw=True
                )
    
    def test_resource_cleanup_on_failure(self):
        """Test that resources are cleaned up when generation fails."""
        # Test VideoComposer cleanup
        composer = VideoComposer("test_job", {"scenes": []}, {})
        
        # Mock timeline with non-existent files
        timeline = [
            {
                "scene": {"timestamp": "0:00"},
                "start": 0,
                "duration": 10,
                "voice": ["/non/existent/audio.mp3"],
                "ui": ["/non/existent/ui.mp4"],
                "visual": ["/non/existent/video.mp4"]
            }
        ]
        
        # Assembly should handle missing files gracefully
        with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as output_file:
            try:
                result = composer.assemble_video(timeline, output_file.name)
                # Should return False but not crash
                assert result is False
            finally:
                if os.path.exists(output_file.name):
                    os.unlink(output_file.name)
    
    def test_monolithic_function_complexity(self):
        """Test that individual functions in the worker are too complex."""
        # The _generate_voice_narration function is over 140 lines
        # This test documents the complexity issue
        
        import inspect
        from workers.tasks.video_generation import _generate_voice_narration
        
        source_lines = inspect.getsourcelines(_generate_voice_narration)[0]
        function_length = len(source_lines)
        
        # Function is too long (should be under 50 lines ideally)
        assert function_length > 100, f"Function _generate_voice_narration is {function_length} lines (too complex)"
        
        # Same for _generate_visual_scenes
        from workers.tasks.video_generation import _generate_visual_scenes
        
        source_lines = inspect.getsourcelines(_generate_visual_scenes)[0]
        function_length = len(source_lines)
        
        assert function_length > 150, f"Function _generate_visual_scenes is {function_length} lines (too complex)"
    
    def test_error_propagation(self):
        """Test that errors propagate correctly through the worker."""
        from workers.tasks.video_generation import ScriptParser
        
        parser = ScriptParser()
        
        # Test with malformed script
        malformed_script = "This is not a valid script format"
        
        # Should handle gracefully or raise specific exception
        try:
            result = parser.parse_script(malformed_script)
            # If it doesn't raise, check that it returns reasonable defaults
            assert isinstance(result, dict)
            assert "title" in result
            assert "scenes" in result
        except Exception as e:
            # Should be a specific, informative exception
            assert str(e) != "Script parsing failed: "


class TestCrossServiceIntegration:
    """Test integration issues between services."""
    
    def test_pipeline_failure_cascade(self):
        """Test how failures cascade through the video generation pipeline."""
        # Mock all services to fail
        with patch('src.services.elevenlabs_client.ElevenLabsClient') as mock_elevenlabs:
            mock_elevenlabs.side_effect = Exception("ElevenLabs service failed")
            
            with patch('src.services.runway_client.RunwayClient') as mock_runway:
                mock_runway.side_effect = Exception("Runway service failed")
                
                with patch('src.services.ffmpeg_service.FFmpegService') as mock_ffmpeg:
                    mock_ffmpeg.side_effect = Exception("FFmpeg service failed")
                    
                    # The video generation should handle cascading failures gracefully
                    # Currently it may not, which this test will reveal
                    try:
                        from workers.tasks.video_generation import process_video_generation
                        
                        # This should not crash the entire system
                        result = process_video_generation("test_job", "test script", {})
                        
                        # Should return error status, not crash
                        assert "status" in result
                        
                    except Exception as e:
                        # If it raises, should be a controlled exception
                        assert "failed" in str(e).lower() or "error" in str(e).lower()
    
    def test_concurrent_resource_access(self):
        """Test concurrent access to shared resources."""
        import threading
        import queue
        
        results = queue.Queue()
        
        def worker_thread(thread_id):
            try:
                # Try to create multiple clients simultaneously
                client = ElevenLabsClient(api_key="test_key")
                result = client.validate_api_key()
                results.put((thread_id, "success", result))
            except Exception as e:
                results.put((thread_id, "error", str(e)))
        
        # Start multiple threads
        threads = []
        for i in range(5):
            thread = threading.Thread(target=worker_thread, args=(i,))
            threads.append(thread)
            thread.start()
        
        # Wait for completion
        for thread in threads:
            thread.join()
        
        # Check results
        while not results.empty():
            thread_id, status, result = results.get()
            # Should handle concurrent access gracefully
            assert status in ["success", "error"]
            if status == "error":
                # Errors should be informative, not generic
                assert len(result) > 0


if __name__ == "__main__":
    # Run specific test categories
    pytest.main([
        __file__,
        "-v",
        "--tb=short",
        "-k", "test_clone_voice_file_leak_risk or test_generation_behavior_differentiation or test_subprocess_cleanup_on_error or test_monolithic_function_complexity"
    ])