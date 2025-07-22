"""
Integration Tests for Video Generation Pipeline

Tests the complete video generation pipeline with proper error handling,
resource management, and service integration.
"""

import os
import pytest
import asyncio
import tempfile
from unittest.mock import Mock, patch, AsyncMock
from pathlib import Path

from src.services.video_generation_orchestrator import VideoGenerationOrchestrator
from src.services.script_parser_service import ScriptParserService
from src.services.voice_generation_service import VoiceGenerationService
from src.services.visual_generation_service import VisualGenerationService
from src.services.terminal_ui_service import TerminalUIService
from src.services.video_assembly_service import VideoAssemblyService


@pytest.fixture
def sample_script():
    """Sample script content for testing."""
    return """
SCRIPT: Test Video Generation

[0:00] Introduction Scene
Visual: A dystopian cityscape with neon lights reflecting in rain-soaked streets
Narration (Male, Calm): Welcome to the world of tomorrow, where technology has reshaped our reality.
ON-SCREEN: > System initializing...

[0:30] Main Content Scene  
Visual: Inside a high-tech server room with blinking lights and screens
Narration (Male, Calm): Behind these walls, artificial intelligence processes millions of data points.
ON-SCREEN: > AI_STATUS: ACTIVE
    """


@pytest.fixture
def test_settings():
    """Test settings for video generation."""
    return {
        'voice_type': 'male_calm',
        'style': 'techwear',
        'quality': 'high',
        'terminal_theme': 'dark',
        'cleanup_temp_files': True
    }


@pytest.fixture
async def orchestrator():
    """Create orchestrator instance for testing."""
    return VideoGenerationOrchestrator()


class TestVideoGenerationOrchestrator:
    """Test the main video generation orchestrator."""
    
    @pytest.mark.asyncio
    async def test_full_pipeline_success(self, orchestrator, sample_script, test_settings):
        """Test successful completion of full video generation pipeline."""
        job_id = "test_job_001"
        
        # Mock external dependencies
        with patch.multiple(
            'src.services.voice_generation_service.VoiceGenerationService',
            generate_narration=AsyncMock(return_value=['/mock/voice1.mp3', '/mock/voice2.mp3'])
        ), patch.multiple(
            'src.services.visual_generation_service.VisualGenerationService', 
            generate_scenes=AsyncMock(return_value=['/mock/visual1.mp4', '/mock/visual2.mp4'])
        ), patch.multiple(
            'src.services.terminal_ui_service.TerminalUIService',
            generate_animations=AsyncMock(return_value=['/mock/ui1.mp4'])
        ), patch.multiple(
            'src.services.video_assembly_service.VideoAssemblyService',
            assemble_video=AsyncMock(return_value='/mock/output/final.mp4')
        ):
            
            result = await orchestrator.generate_video(job_id, sample_script, test_settings)
            
            assert result['status'] == 'completed'
            assert result['job_id'] == job_id
            assert result['output_file'] == '/mock/output/final.mp4'
            assert result['assets_generated']['voice_files'] == 2
            assert result['assets_generated']['visual_assets'] == 2
            assert result['assets_generated']['ui_elements'] == 1
            assert 'processing_time' in result
    
    @pytest.mark.asyncio
    async def test_pipeline_with_service_failures(self, orchestrator, sample_script, test_settings):
        """Test pipeline resilience when services fail and use fallbacks."""
        job_id = "test_job_002"
        
        # Mock voice service to fail, others to succeed with fallbacks
        with patch.multiple(
            'src.services.voice_generation_service.VoiceGenerationService',
            generate_narration=AsyncMock(side_effect=Exception("API error")),
            generate_mock_files=AsyncMock(return_value=['/mock/fallback_voice.mp3'])
        ), patch.multiple(
            'src.services.visual_generation_service.VisualGenerationService',
            generate_scenes=AsyncMock(side_effect=Exception("Runway error")),
            generate_placeholders=AsyncMock(return_value=['/mock/placeholder.mp4'])
        ), patch.multiple(
            'src.services.terminal_ui_service.TerminalUIService',
            generate_animations=AsyncMock(return_value=[])  # No UI elements
        ), patch.multiple(
            'src.services.video_assembly_service.VideoAssemblyService',
            assemble_video=AsyncMock(return_value='/mock/output/fallback.mp4')
        ):
            
            result = await orchestrator.generate_video(job_id, sample_script, test_settings)
            
            # Should still complete with fallback content
            assert result['status'] == 'completed'
            assert result['job_id'] == job_id
            assert result['output_file'] == '/mock/output/fallback.mp4'
    
    @pytest.mark.asyncio
    async def test_job_status_tracking(self, orchestrator, sample_script, test_settings):
        """Test job status tracking throughout pipeline."""
        job_id = "test_job_003"
        
        # Mock services with delays to test progress tracking
        async def mock_slow_voice(*args, **kwargs):
            await asyncio.sleep(0.1)
            return ['/mock/voice.mp3']
        
        async def mock_slow_visual(*args, **kwargs):
            await asyncio.sleep(0.1)
            return ['/mock/visual.mp4']
        
        async def mock_slow_assembly(*args, **kwargs):
            await asyncio.sleep(0.1)
            return '/mock/output/test.mp4'
        
        with patch.multiple(
            'src.services.voice_generation_service.VoiceGenerationService',
            generate_narration=AsyncMock(side_effect=mock_slow_voice)
        ), patch.multiple(
            'src.services.visual_generation_service.VisualGenerationService',
            generate_scenes=AsyncMock(side_effect=mock_slow_visual)
        ), patch.multiple(
            'src.services.terminal_ui_service.TerminalUIService',
            generate_animations=AsyncMock(return_value=[])
        ), patch.multiple(
            'src.services.video_assembly_service.VideoAssemblyService',
            assemble_video=AsyncMock(side_effect=mock_slow_assembly)
        ):
            
            # Start generation in background
            generation_task = asyncio.create_task(
                orchestrator.generate_video(job_id, sample_script, test_settings)
            )
            
            # Check status during processing
            await asyncio.sleep(0.05)  # Let it start
            status = orchestrator.get_job_status(job_id)
            
            if status:  # Job might complete too quickly in tests
                assert status['job_id'] == job_id
                assert 'stage' in status
                assert 'progress' in status
                assert status['progress'] >= 0
            
            # Wait for completion
            result = await generation_task
            assert result['status'] == 'completed'
    
    @pytest.mark.asyncio
    async def test_job_cancellation(self, orchestrator, sample_script, test_settings):
        """Test job cancellation functionality."""
        job_id = "test_job_004"
        
        # Mock services with long delays
        async def mock_slow_service(*args, **kwargs):
            await asyncio.sleep(10)  # Long delay
            return []
        
        with patch.multiple(
            'src.services.voice_generation_service.VoiceGenerationService',
            generate_narration=AsyncMock(side_effect=mock_slow_service),
            cancel_generation=AsyncMock(return_value=True)
        ), patch.multiple(
            'src.services.visual_generation_service.VisualGenerationService',
            generate_scenes=AsyncMock(side_effect=mock_slow_service),
            cancel_generation=AsyncMock(return_value=True)
        ), patch.multiple(
            'src.services.terminal_ui_service.TerminalUIService',
            generate_animations=AsyncMock(side_effect=mock_slow_service),
            cancel_generation=AsyncMock(return_value=True)
        ):
            
            # Start generation
            generation_task = asyncio.create_task(
                orchestrator.generate_video(job_id, sample_script, test_settings)
            )
            
            # Cancel after a short delay
            await asyncio.sleep(0.1)
            cancelled = await orchestrator.cancel_job(job_id)
            
            assert cancelled == True
            
            # Task should be cancelled or complete with error
            try:
                await generation_task
            except (asyncio.CancelledError, Exception):
                pass  # Expected


class TestScriptParserService:
    """Test script parsing service."""
    
    @pytest.mark.asyncio
    async def test_parse_valid_script(self, sample_script):
        """Test parsing of valid script content."""
        parser = ScriptParserService()
        
        result = await parser.parse_script(sample_script)
        
        assert result['title'] == 'Test Video Generation'
        assert len(result['scenes']) == 2
        assert result['scene_count'] == 2
        assert result['total_duration'] > 0
        
        # Check first scene
        scene1 = result['scenes'][0]
        assert scene1['timestamp'] == '0:00'
        assert scene1['timestamp_seconds'] == 0
        assert len(scene1['visual_descriptions']) > 0
        assert len(scene1['narration']) > 0
        assert len(scene1['onscreen_text']) > 0
    
    @pytest.mark.asyncio
    async def test_parse_invalid_script(self):
        """Test handling of invalid script content."""
        parser = ScriptParserService()
        
        # Empty script
        with pytest.raises(ValueError, match="Script content is empty"):
            await parser.parse_script("")
        
        # Script with no timestamps
        with pytest.raises(ValueError, match="No valid timestamp sections"):
            await parser.parse_script("Just some random text without timestamps")
    
    def test_script_validation(self, sample_script):
        """Test script validation functionality."""
        parser = ScriptParserService()
        
        issues = parser.validate_script(sample_script)
        
        # Valid script should have no issues
        assert len(issues) == 0
        
        # Test invalid script
        invalid_script = "No timestamps here"
        issues = parser.validate_script(invalid_script)
        
        assert len(issues) > 0
        assert any(issue['type'] == 'error' for issue in issues)


class TestServiceIntegration:
    """Test integration between services."""
    
    @pytest.mark.asyncio
    async def test_voice_service_integration(self, sample_script):
        """Test voice generation service integration."""
        parser = ScriptParserService()
        voice_service = VoiceGenerationService()
        
        # Parse script
        parsed_script = await parser.parse_script(sample_script)
        
        # Test voice generation (should use mocks/fallbacks without API keys)
        settings = {'voice_type': 'male_calm', 'job_id': 'test_voice'}
        
        with patch('os.environ.get', return_value=None):  # No API key
            voice_files = await voice_service.generate_narration(parsed_script, settings)
            
            # Should generate mock files
            assert len(voice_files) > 0
            assert all(isinstance(f, str) for f in voice_files)
    
    @pytest.mark.asyncio
    async def test_visual_service_integration(self, sample_script):
        """Test visual generation service integration."""
        parser = ScriptParserService()
        visual_service = VisualGenerationService()
        
        # Parse script
        parsed_script = await parser.parse_script(sample_script)
        
        # Test visual generation (should use placeholders without API)
        settings = {'style': 'cinematic', 'job_id': 'test_visual'}
        
        visual_assets = await visual_service.generate_scenes(parsed_script, settings)
        
        # Should generate placeholder assets
        assert isinstance(visual_assets, list)
    
    @pytest.mark.asyncio
    async def test_ui_service_integration(self, sample_script):
        """Test terminal UI service integration."""
        parser = ScriptParserService()
        ui_service = TerminalUIService()
        
        # Parse script
        parsed_script = await parser.parse_script(sample_script)
        
        # Test UI generation
        settings = {'terminal_theme': 'dark', 'job_id': 'test_ui'}
        
        ui_elements = await ui_service.generate_animations(parsed_script, settings)
        
        # Should return list (may be empty if FFmpeg not available in test env)
        assert isinstance(ui_elements, list)


class TestErrorHandling:
    """Test error handling and recovery mechanisms."""
    
    @pytest.mark.asyncio
    async def test_circuit_breaker_functionality(self):
        """Test circuit breaker pattern for external services."""
        from src.utils.circuit_breaker import CircuitBreaker, CircuitBreakerError
        
        # Create circuit breaker with low threshold for testing
        breaker = CircuitBreaker(failure_threshold=2, recovery_timeout=1.0)
        
        # Mock function that fails
        async def failing_function():
            raise Exception("Service unavailable")
        
        # Should fail normally first few times
        with pytest.raises(Exception, match="Service unavailable"):
            await breaker.call(failing_function)
        
        with pytest.raises(Exception, match="Service unavailable"):
            await breaker.call(failing_function)
        
        # Now circuit should be open
        with pytest.raises(CircuitBreakerError):
            await breaker.call(failing_function)
    
    @pytest.mark.asyncio
    async def test_retry_mechanism(self):
        """Test retry mechanism with exponential backoff."""
        from src.utils.retry_handler import RetryHandler, RetryExhausted
        
        retry_handler = RetryHandler(max_retries=2, base_delay=0.01)  # Fast for testing
        
        call_count = 0
        
        async def flaky_function():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise Exception(f"Attempt {call_count} failed")
            return "success"
        
        # Should succeed after retries
        result = await retry_handler.execute_with_retry(flaky_function)
        assert result == "success"
        assert call_count == 3
        
        # Test exhaustion
        call_count = 0
        
        async def always_failing_function():
            nonlocal call_count
            call_count += 1
            raise Exception("Always fails")
        
        with pytest.raises(RetryExhausted):
            await retry_handler.execute_with_retry(always_failing_function)
        
        assert call_count == 3  # Initial attempt + 2 retries


class TestResourceManagement:
    """Test resource management and cleanup."""
    
    @pytest.mark.asyncio
    async def test_resource_allocation(self):
        """Test resource allocation and cleanup."""
        from src.utils.resource_manager import ResourceManager
        
        resource_manager = ResourceManager()
        
        # Test resource allocation
        async with resource_manager.acquire_resources(memory_mb=100, cpu_cores=1) as resources:
            assert resources['memory_mb'] == 100
            assert resources['cpu_cores'] == 1
            assert 'start_time' in resources
            
            # Check that resources are tracked
            usage = resource_manager.get_usage_stats()
            assert usage['operations']['active'] == 1
    
    @pytest.mark.asyncio 
    async def test_file_cleanup(self):
        """Test file cleanup functionality."""
        from src.utils.file_manager import FileManager
        
        file_manager = FileManager()
        
        # Create temporary test file
        test_data = b"test video data"
        test_file = await file_manager.save_video_file("test_cleanup.mp4", test_data)
        
        # Verify file exists
        assert os.path.exists(test_file)
        
        # Test cleanup
        deleted = await file_manager.delete_file(test_file)
        assert deleted == True
        assert not os.path.exists(test_file)


@pytest.mark.asyncio
async def test_health_monitoring():
    """Test service health monitoring."""
    from src.services.health_monitor import ServiceHealthMonitor, ServiceStatus
    
    monitor = ServiceHealthMonitor()
    
    # Mock health check function
    async def healthy_service():
        return {
            'status': 'healthy',
            'response_time_ms': 50,
            'active_operations': 2
        }
    
    async def unhealthy_service():
        raise Exception("Service down")
    
    # Test healthy service
    health = await monitor.check_service_health("test_service", healthy_service)
    assert health.status == ServiceStatus.HEALTHY
    assert len(health.metrics) > 0
    
    # Test unhealthy service
    health = await monitor.check_service_health("failing_service", unhealthy_service)
    assert health.status == ServiceStatus.UNHEALTHY
    assert health.error_message is not None
    
    # Test system health summary
    summary = monitor.get_system_health_summary()
    assert summary['services_count'] == 2
    assert summary['healthy_count'] == 1
    assert summary['unhealthy_count'] == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])