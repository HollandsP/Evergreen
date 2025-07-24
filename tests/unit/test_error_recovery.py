"""
Comprehensive tests for error recovery components
"""

import pytest
import asyncio
import os
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime, timedelta

# Import our error recovery components
from src.utils.retry_manager import (
    IntelligentRetryManager, RetryContext, RetryStrategy, 
    OperationType, retry_with_context
)
from src.services.error_context_logger import (
    ErrorContextLogger, ErrorSeverity, ErrorCategory,
    error_logger, log_errors
)
from src.services.corruption_detector import (
    CorruptionDetector, FileType, IntegrityStatus, FileIntegrityInfo
)
from src.services.graceful_degradation import (
    GracefulDegradationService, ServiceLevel, DegradationReason,
    ServiceAdapter
)


class TestIntelligentRetryManager:
    """Test the retry manager with various scenarios."""
    
    @pytest.fixture
    def retry_manager(self):
        return IntelligentRetryManager(
            default_strategy=RetryStrategy.STANDARD,
            max_retries=3,
            base_delay=0.1,  # Short delays for testing
            max_delay=1.0
        )
    
    @pytest.mark.asyncio
    async def test_successful_operation(self, retry_manager):
        """Test successful operation without retries."""
        call_count = 0
        
        async def successful_op():
            nonlocal call_count
            call_count += 1
            return "success"
        
        context = RetryContext(
            operation_id="test-1",
            operation_type=OperationType.API_CALL,
            resource_usage={'cpu': 50, 'memory': 60},
            failure_history=[],
            priority=5
        )
        
        result = await retry_manager.execute_with_retry(successful_op, context)
        assert result == "success"
        assert call_count == 1
    
    @pytest.mark.asyncio
    async def test_retry_with_recovery(self, retry_manager):
        """Test operation that fails then succeeds."""
        call_count = 0
        
        async def flaky_op():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ConnectionError("Network error")
            return "success"
        
        context = RetryContext(
            operation_id="test-2",
            operation_type=OperationType.API_CALL,
            resource_usage={'cpu': 50, 'memory': 60},
            failure_history=[],
            priority=5
        )
        
        result = await retry_manager.execute_with_retry(flaky_op, context)
        assert result == "success"
        assert call_count == 3
        
        # Check metrics
        metrics = retry_manager.get_metrics_summary()
        assert metrics['by_type']['api_call']['successful_retries'] > 0
    
    @pytest.mark.asyncio
    async def test_non_retryable_error(self, retry_manager):
        """Test that certain errors are not retried."""
        call_count = 0
        
        async def bad_input_op():
            nonlocal call_count
            call_count += 1
            raise ValueError("Invalid input")
        
        context = RetryContext(
            operation_id="test-3",
            operation_type=OperationType.API_CALL,
            resource_usage={'cpu': 50, 'memory': 60},
            failure_history=[],
            priority=5
        )
        
        with pytest.raises(ValueError):
            await retry_manager.execute_with_retry(bad_input_op, context)
        
        assert call_count == 1  # Should not retry
    
    @pytest.mark.asyncio
    async def test_resource_aware_retry(self, retry_manager):
        """Test resource-aware retry behavior."""
        with patch('psutil.cpu_percent', return_value=95):
            with patch('psutil.virtual_memory') as mock_mem:
                mock_mem.return_value.percent = 95
                
                context = RetryContext(
                    operation_id="test-4",
                    operation_type=OperationType.VIDEO_PROCESSING,
                    resource_usage={'cpu': 95, 'memory': 95},
                    failure_history=[],
                    priority=5
                )
                
                # Should wait for resources
                waited = False
                
                async def resource_intensive_op():
                    nonlocal waited
                    if not waited:
                        waited = True
                        raise MemoryError("Out of memory")
                    return "success"
                
                # This should use conservative strategy due to high resource usage
                strategy = retry_manager._determine_strategy(context)
                assert strategy == RetryStrategy.CONSERVATIVE
    
    @pytest.mark.asyncio
    async def test_deadline_aware_retry(self, retry_manager):
        """Test deadline-aware retry behavior."""
        context = RetryContext(
            operation_id="test-5",
            operation_type=OperationType.API_CALL,
            resource_usage={'cpu': 50, 'memory': 60},
            failure_history=[],
            priority=8,
            deadline=datetime.now() + timedelta(seconds=2)
        )
        
        call_count = 0
        
        async def slow_op():
            nonlocal call_count
            call_count += 1
            await asyncio.sleep(0.5)
            raise TimeoutError("Too slow")
        
        with pytest.raises(Exception):
            await retry_manager.execute_with_retry(slow_op, context)
        
        # Should have limited retries due to deadline
        assert call_count <= 3
    
    @pytest.mark.asyncio
    async def test_decorator_usage(self):
        """Test the retry decorator."""
        call_count = 0
        
        @retry_with_context(OperationType.API_CALL, priority=7)
        async def decorated_function():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise ConnectionError("Network error")
            return "success"
        
        result = await decorated_function()
        assert result == "success"
        assert call_count == 2


class TestErrorContextLogger:
    """Test the error context logger."""
    
    @pytest.fixture
    def logger(self):
        return ErrorContextLogger(
            app_name="test-app",
            environment="test"
        )
    
    @pytest.mark.asyncio
    async def test_error_logging(self, logger):
        """Test basic error logging."""
        error = ValueError("Test error")
        
        context = await logger.log_error(
            exception=error,
            severity=ErrorSeverity.ERROR,
            category=ErrorCategory.VALIDATION_ERROR,
            operation="test_operation",
            user_id="user123",
            input_data={"key": "value"}
        )
        
        assert context.error_type == "ValueError"
        assert context.error_message == "Test error"
        assert context.category == ErrorCategory.VALIDATION_ERROR
        assert context.user_id == "user123"
        assert context.suggested_action is not None
    
    @pytest.mark.asyncio
    async def test_correlation_tracking(self, logger):
        """Test correlation ID tracking."""
        correlation_id = logger.set_correlation_id()
        
        # Log multiple errors with same correlation
        error1 = await logger.log_error(
            exception=ValueError("Error 1"),
            operation="op1"
        )
        
        error2 = await logger.log_error(
            exception=RuntimeError("Error 2"),
            operation="op2"
        )
        
        # Check correlation chain
        chain = logger.get_correlation_chain(correlation_id)
        assert len(chain) == 2
        assert chain[0].correlation_id == chain[1].correlation_id
    
    @pytest.mark.asyncio
    async def test_error_categorization(self, logger):
        """Test automatic error categorization."""
        test_cases = [
            (ConnectionError("Network timeout"), ErrorCategory.NETWORK_ERROR),
            (PermissionError("Access denied"), ErrorCategory.PERMISSION_ERROR),
            (ValueError("Invalid format"), ErrorCategory.VALIDATION_ERROR),
            (Exception("Database connection failed"), ErrorCategory.DATABASE_ERROR),
            (Exception("API rate limit exceeded"), ErrorCategory.API_ERROR)
        ]
        
        for error, expected_category in test_cases:
            context = await logger.log_error(error)
            assert context.category == expected_category
    
    @pytest.mark.asyncio
    async def test_sensitive_data_sanitization(self, logger):
        """Test that sensitive data is sanitized."""
        error = ValueError("Test error")
        
        context = await logger.log_error(
            exception=error,
            input_data={
                "username": "test_user",
                "password": "secret123",
                "api_key": "sk-1234567890",
                "data": "normal data"
            }
        )
        
        assert context.input_data["username"] == "test_user"
        assert context.input_data["password"] == "[REDACTED]"
        assert context.input_data["api_key"] == "[REDACTED]"
        assert context.input_data["data"] == "normal data"
    
    def test_error_summary(self, logger):
        """Test error summary generation."""
        # Add some test errors
        asyncio.run(logger.log_error(ValueError("Error 1")))
        asyncio.run(logger.log_error(ValueError("Error 2")))
        asyncio.run(logger.log_error(RuntimeError("Error 3")))
        
        summary = logger.get_error_summary(hours=24)
        
        assert summary['total_errors'] == 3
        assert 'ValueError' in [e[0] for e in summary['top_errors']]
        assert summary['error_rate'] > 0
    
    @pytest.mark.asyncio
    async def test_decorator_error_logging(self):
        """Test the error logging decorator."""
        @log_errors(severity=ErrorSeverity.WARNING)
        async def failing_function():
            raise RuntimeError("Decorated error")
        
        with pytest.raises(RuntimeError):
            await failing_function()
        
        # Error should be logged
        summary = error_logger.get_error_summary(hours=1)
        assert summary['total_errors'] > 0


class TestCorruptionDetector:
    """Test the file corruption detector."""
    
    @pytest.fixture
    def detector(self, tmp_path):
        return CorruptionDetector(
            quarantine_dir=str(tmp_path / "quarantine"),
            backup_dir=str(tmp_path / "backups"),
            enable_auto_backup=True
        )
    
    @pytest.mark.asyncio
    async def test_valid_file_check(self, detector, tmp_path):
        """Test checking a valid file."""
        # Create a test file
        test_file = tmp_path / "test.txt"
        test_file.write_text("This is a test file")
        
        info = await detector.check_file_integrity(test_file)
        
        assert info.status == IntegrityStatus.VALID
        assert info.file_type == FileType.DOCUMENT
        assert info.md5_hash is not None
        assert info.sha256_hash is not None
    
    @pytest.mark.asyncio
    async def test_corrupted_file_detection(self, detector, tmp_path):
        """Test detecting a corrupted file."""
        # Create a fake corrupted image file
        test_file = tmp_path / "corrupted.jpg"
        test_file.write_bytes(b"not a real image")
        
        with patch('magic.Magic.from_file', return_value='image/jpeg'):
            info = await detector.check_file_integrity(test_file)
            
            assert info.status in [
                IntegrityStatus.CORRUPTED,
                IntegrityStatus.PARTIALLY_CORRUPTED
            ]
            assert info.corruption_type is not None
    
    @pytest.mark.asyncio
    async def test_backup_creation(self, detector, tmp_path):
        """Test automatic backup creation."""
        # Create a test file
        test_file = tmp_path / "important.txt"
        test_file.write_text("Important data")
        
        info = await detector.check_file_integrity(
            test_file,
            create_backup=True
        )
        
        assert info.backup_available
        
        # Check backup exists
        backup_files = list(detector.backup_dir.glob("important_*.txt"))
        assert len(backup_files) > 0
    
    @pytest.mark.asyncio
    async def test_file_quarantine(self, detector, tmp_path):
        """Test quarantining corrupted files."""
        # Create a test file
        test_file = tmp_path / "infected.txt"
        test_file.write_text("Corrupted content")
        
        await detector.quarantine_file(test_file, "Test quarantine")
        
        # Check file moved to quarantine
        assert not test_file.exists()
        quarantine_files = list(detector.quarantine_dir.glob("infected_*_CORRUPTED.txt"))
        assert len(quarantine_files) > 0
        
        # Check quarantine info exists
        info_files = list(detector.quarantine_dir.glob("*.json"))
        assert len(info_files) > 0
    
    @pytest.mark.asyncio
    async def test_file_recovery(self, detector, tmp_path):
        """Test file recovery from backup."""
        # Create and backup a file
        test_file = tmp_path / "recover.txt"
        test_file.write_text("Original content")
        
        # Create backup
        info = await detector.check_file_integrity(
            test_file,
            create_backup=True
        )
        
        # Corrupt the file
        test_file.write_text("Corrupted!")
        
        # Attempt recovery
        recovered_path = await detector.recover_file(test_file)
        
        assert recovered_path is not None
        assert recovered_path.read_text() == "Original content"
    
    def test_integrity_report(self, detector):
        """Test integrity report generation."""
        report = detector.get_integrity_report()
        
        assert 'total_files_checked' in report
        assert 'status_distribution' in report
        assert 'corruption_rate' in report
        assert 'backup_count' in report


class TestGracefulDegradation:
    """Test the graceful degradation service."""
    
    @pytest.fixture
    def degradation_service(self):
        service = GracefulDegradationService(
            default_level=ServiceLevel.FULL,
            auto_recovery=True,
            monitoring_interval=1  # Short interval for testing
        )
        return service
    
    @pytest.mark.asyncio
    async def test_service_level_change(self, degradation_service):
        """Test changing service levels."""
        # Change to reduced level
        await degradation_service.set_service_level(
            ServiceLevel.REDUCED,
            DegradationReason.HIGH_LOAD
        )
        
        assert degradation_service.current_level == ServiceLevel.REDUCED
        assert not degradation_service.feature_flags['real_time_preview']
    
    @pytest.mark.asyncio
    async def test_automatic_degradation(self, degradation_service):
        """Test automatic degradation based on metrics."""
        # Simulate high CPU usage
        with patch('psutil.cpu_percent', return_value=85):
            with patch('psutil.virtual_memory') as mock_mem:
                mock_mem.return_value.percent = 70
                
                # Start monitoring
                await degradation_service.start_monitoring()
                
                # Wait for monitoring cycle
                await asyncio.sleep(2)
                
                # Should have degraded
                assert degradation_service.current_level != ServiceLevel.FULL
                
                # Stop monitoring
                await degradation_service.stop_monitoring()
    
    def test_feature_flag_management(self, degradation_service):
        """Test feature flag management."""
        # Check initial state
        assert degradation_service.is_feature_enabled('ai_generation')
        
        # Disable feature
        degradation_service.feature_flags['ai_generation'] = False
        assert not degradation_service.is_feature_enabled('ai_generation')
    
    def test_quality_settings_reduction(self, degradation_service):
        """Test quality settings reduction."""
        initial_resolution = degradation_service.get_quality_setting('video_resolution')
        
        # Reduce quality
        asyncio.run(degradation_service._reduce_quality_settings())
        
        new_resolution = degradation_service.get_quality_setting('video_resolution')
        assert new_resolution != initial_resolution
        assert new_resolution == '1280x720'
    
    @pytest.mark.asyncio
    async def test_service_adapter_integration(self, degradation_service):
        """Test service adapter integration."""
        # Create mock adapter
        class MockAdapter(ServiceAdapter):
            def __init__(self):
                self.level = ServiceLevel.FULL
            
            async def adapt_to_level(self, level: ServiceLevel) -> bool:
                self.level = level
                return True
            
            def get_current_capabilities(self) -> Dict[str, Any]:
                return {"level": self.level.value}
        
        # Register adapter
        adapter = MockAdapter()
        degradation_service.register_service("mock_service", adapter)
        
        # Change level
        await degradation_service.set_service_level(ServiceLevel.MINIMAL)
        
        # Check adapter was notified
        assert adapter.level == ServiceLevel.MINIMAL
    
    @pytest.mark.asyncio
    async def test_forced_degradation(self, degradation_service):
        """Test forced degradation with recovery."""
        # Force degradation for 1 second
        await degradation_service.force_degradation(
            ServiceLevel.EMERGENCY,
            duration_minutes=0.0167  # 1 second
        )
        
        assert degradation_service.current_level == ServiceLevel.EMERGENCY
        
        # Wait for recovery
        await asyncio.sleep(2)
        
        # Should have recovered
        assert degradation_service.current_level == ServiceLevel.FULL
    
    def test_status_reporting(self, degradation_service):
        """Test status reporting."""
        status = degradation_service.get_status()
        
        assert 'current_level' in status
        assert 'feature_flags' in status
        assert 'quality_settings' in status
        assert status['current_level'] == 'full'


@pytest.mark.integration
class TestErrorRecoveryIntegration:
    """Integration tests for error recovery components."""
    
    @pytest.mark.asyncio
    async def test_retry_with_logging(self):
        """Test retry manager with error logging integration."""
        retry_manager = IntelligentRetryManager()
        logger = ErrorContextLogger()
        
        call_count = 0
        
        async def flaky_operation():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                error = ConnectionError("API timeout")
                await logger.log_error(
                    error,
                    operation="flaky_operation",
                    severity=ErrorSeverity.WARNING
                )
                raise error
            return "success"
        
        context = RetryContext(
            operation_id="integration-test",
            operation_type=OperationType.API_CALL,
            resource_usage={'cpu': 50, 'memory': 60},
            failure_history=[],
            priority=5
        )
        
        result = await retry_manager.execute_with_retry(
            flaky_operation,
            context
        )
        
        assert result == "success"
        
        # Check error was logged
        summary = logger.get_error_summary(hours=1)
        assert summary['total_errors'] >= 2
    
    @pytest.mark.asyncio
    async def test_degradation_with_retry(self):
        """Test degradation service with retry behavior."""
        degradation_service = GracefulDegradationService()
        retry_manager = IntelligentRetryManager()
        
        # Set to reduced service level
        await degradation_service.set_service_level(ServiceLevel.REDUCED)
        
        # Create operation that respects degradation
        async def degradation_aware_operation():
            if not degradation_service.is_feature_enabled('advanced_effects'):
                return "basic_result"
            return "advanced_result"
        
        context = RetryContext(
            operation_id="degradation-test",
            operation_type=OperationType.VIDEO_PROCESSING,
            resource_usage={'cpu': 50, 'memory': 60},
            failure_history=[],
            priority=5
        )
        
        result = await retry_manager.execute_with_retry(
            degradation_aware_operation,
            context
        )
        
        assert result == "basic_result"  # Advanced effects disabled
    
    @pytest.mark.asyncio
    async def test_corruption_recovery_with_retry(self, tmp_path):
        """Test corruption detection with retry on recovery."""
        detector = CorruptionDetector(
            quarantine_dir=str(tmp_path / "quarantine"),
            backup_dir=str(tmp_path / "backups")
        )
        retry_manager = IntelligentRetryManager()
        
        # Create test file
        test_file = tmp_path / "data.txt"
        test_file.write_text("Important data")
        
        # Create backup
        await detector.check_file_integrity(test_file, create_backup=True)
        
        # Corrupt file
        test_file.write_text("Corrupted!")
        
        # Recovery operation with retry
        async def recover_with_retry():
            recovered = await detector.recover_file(test_file)
            if recovered is None:
                raise RuntimeError("Recovery failed")
            return recovered
        
        context = RetryContext(
            operation_id="recovery-test",
            operation_type=OperationType.FILE_OPERATION,
            resource_usage={'cpu': 50, 'memory': 60},
            failure_history=[],
            priority=8
        )
        
        recovered_path = await retry_manager.execute_with_retry(
            recover_with_retry,
            context
        )
        
        assert recovered_path is not None
        assert recovered_path.read_text() == "Important data"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])