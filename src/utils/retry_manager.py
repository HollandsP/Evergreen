"""
Enhanced Retry Manager with Intelligent Backoff and Recovery

Provides bulletproof retry mechanisms with:
- Smart exponential backoff with jitter
- Operation context awareness
- Predictive failure detection
- Graceful degradation strategies
- Resource-aware retry decisions
"""

import asyncio
import random
import time
import hashlib
import json
from typing import Any, Callable, Optional, Type, Union, List, Dict, Tuple
from functools import wraps
import zlib
from enum import Enum
from dataclasses import dataclass
from datetime import datetime, timedelta

import structlog
from tenacity import RetryError, Retrying, stop_after_attempt, wait_exponential_jitter
import aiohttp
import psutil

logger = structlog.get_logger()


class RetryStrategy(Enum):
    """Different retry strategies based on operation type."""
    AGGRESSIVE = "aggressive"      # Quick retries for critical operations
    STANDARD = "standard"          # Normal exponential backoff
    CONSERVATIVE = "conservative"  # Slower retries for resource-intensive ops
    ADAPTIVE = "adaptive"         # Dynamically adjusts based on system state


class OperationType(Enum):
    """Types of operations for context-aware retry logic."""
    API_CALL = "api_call"
    FILE_OPERATION = "file_operation"
    DATABASE_QUERY = "database_query"
    VIDEO_PROCESSING = "video_processing"
    MEMORY_INTENSIVE = "memory_intensive"
    NETWORK_REQUEST = "network_request"


@dataclass
class RetryContext:
    """Context information for intelligent retry decisions."""
    operation_id: str
    operation_type: OperationType
    resource_usage: Dict[str, float]
    failure_history: List[Dict[str, Any]]
    priority: int = 5  # 1-10, higher is more important
    deadline: Optional[datetime] = None
    user_visible: bool = True
    data_size: Optional[int] = None
    
    
@dataclass
class RetryMetrics:
    """Metrics for retry operations."""
    total_attempts: int = 0
    successful_retries: int = 0
    failed_retries: int = 0
    total_delay_time: float = 0.0
    average_delay: float = 0.0
    success_rate: float = 0.0
    last_updated: datetime = None


class IntelligentRetryManager:
    """
    Advanced retry manager with intelligent backoff and system awareness.
    
    Features:
    - Context-aware retry strategies
    - Resource monitoring for smart decisions
    - Predictive failure detection
    - Operation prioritization
    - Detailed metrics and logging
    """
    
    def __init__(self, 
                 default_strategy: RetryStrategy = RetryStrategy.STANDARD,
                 max_retries: int = 5,
                 base_delay: float = 1.0,
                 max_delay: float = 300.0,
                 resource_threshold: float = 80.0):
        """
        Initialize intelligent retry manager.
        
        Args:
            default_strategy: Default retry strategy
            max_retries: Maximum retry attempts
            base_delay: Base delay between retries
            max_delay: Maximum delay between retries
            resource_threshold: CPU/memory threshold for conservative retries
        """
        self.default_strategy = default_strategy
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.resource_threshold = resource_threshold
        
        # Metrics tracking
        self.metrics: Dict[str, RetryMetrics] = {}
        self.operation_history: List[Dict[str, Any]] = []
        
        # Strategy configurations
        self.strategy_configs = {
            RetryStrategy.AGGRESSIVE: {
                'max_retries': 10,
                'base_delay': 0.5,
                'max_delay': 30.0,
                'backoff_factor': 1.5,
                'jitter': 0.1
            },
            RetryStrategy.STANDARD: {
                'max_retries': 5,
                'base_delay': 1.0,
                'max_delay': 60.0,
                'backoff_factor': 2.0,
                'jitter': 0.25
            },
            RetryStrategy.CONSERVATIVE: {
                'max_retries': 3,
                'base_delay': 5.0,
                'max_delay': 300.0,
                'backoff_factor': 3.0,
                'jitter': 0.5
            }
        }
        
        logger.info(
            "Intelligent retry manager initialized",
            default_strategy=default_strategy.value,
            max_retries=max_retries,
            resource_threshold=resource_threshold
        )
    
    async def execute_with_retry(self, 
                               func: Callable,
                               context: RetryContext,
                               *args,
                               custom_strategy: Optional[RetryStrategy] = None,
                               **kwargs) -> Any:
        """
        Execute function with intelligent retry logic.
        
        Args:
            func: Function to execute
            context: Retry context information
            custom_strategy: Override strategy for this operation
            
        Returns:
            Function result
            
        Raises:
            Exception: When all retries exhausted or operation not recoverable
        """
        start_time = time.time()
        strategy = custom_strategy or self._determine_strategy(context)
        config = self._get_strategy_config(strategy, context)
        
        logger.info(
            "Starting retry-enabled operation",
            operation_id=context.operation_id,
            operation_type=context.operation_type.value,
            strategy=strategy.value,
            priority=context.priority,
            user_visible=context.user_visible
        )
        
        attempt = 0
        last_exception = None
        
        while attempt <= config['max_retries']:
            try:
                # Check system resources before attempting
                if not self._check_resources(context):
                    await self._wait_for_resources(context)
                
                # Log attempt
                logger.debug(
                    "Attempting operation",
                    operation_id=context.operation_id,
                    attempt=attempt + 1,
                    max_attempts=config['max_retries'] + 1
                )
                
                # Execute the function
                if asyncio.iscoroutinefunction(func):
                    result = await func(*args, **kwargs)
                else:
                    result = await asyncio.get_event_loop().run_in_executor(
                        None, func, *args, **kwargs
                    )
                
                # Success - update metrics
                self._record_success(context, attempt, time.time() - start_time)
                
                if attempt > 0:
                    logger.info(
                        "Operation succeeded after retries",
                        operation_id=context.operation_id,
                        attempts=attempt + 1,
                        total_time=time.time() - start_time
                    )
                
                return result
                
            except Exception as e:
                last_exception = e
                attempt += 1
                
                # Record failure
                self._record_failure(context, e, attempt)
                
                # Check if we should retry
                if not self._should_retry(e, context, attempt, config):
                    logger.error(
                        "Operation failed - not retryable",
                        operation_id=context.operation_id,
                        error=str(e),
                        error_type=type(e).__name__,
                        attempts=attempt
                    )
                    raise e
                
                # Check if we've exhausted retries
                if attempt > config['max_retries']:
                    logger.error(
                        "Operation failed - retries exhausted",
                        operation_id=context.operation_id,
                        error=str(e),
                        attempts=attempt,
                        total_time=time.time() - start_time
                    )
                    raise self._create_enhanced_error(e, context, attempt)
                
                # Calculate delay
                delay = self._calculate_delay(attempt, config, context)
                
                # Log retry attempt
                logger.warning(
                    "Operation failed - retrying",
                    operation_id=context.operation_id,
                    error=str(e),
                    error_type=type(e).__name__,
                    attempt=attempt,
                    retry_delay=delay,
                    next_attempt=attempt + 1
                )
                
                # Wait before retry
                await asyncio.sleep(delay)
        
        # Should not reach here
        raise self._create_enhanced_error(last_exception, context, attempt)
    
    def _determine_strategy(self, context: RetryContext) -> RetryStrategy:
        """Determine optimal retry strategy based on context."""
        # Check for adaptive strategy
        if self.default_strategy == RetryStrategy.ADAPTIVE:
            # High priority operations get aggressive retries
            if context.priority >= 8:
                return RetryStrategy.AGGRESSIVE
            
            # Resource-intensive operations get conservative retries
            if context.operation_type in [
                OperationType.VIDEO_PROCESSING,
                OperationType.MEMORY_INTENSIVE
            ]:
                return RetryStrategy.CONSERVATIVE
            
            # Check system resources
            cpu_percent = psutil.cpu_percent(interval=0.1)
            memory_percent = psutil.virtual_memory().percent
            
            if cpu_percent > self.resource_threshold or memory_percent > self.resource_threshold:
                return RetryStrategy.CONSERVATIVE
            
            # Default to standard
            return RetryStrategy.STANDARD
        
        return self.default_strategy
    
    def _get_strategy_config(self, strategy: RetryStrategy, context: RetryContext) -> Dict[str, Any]:
        """Get configuration for retry strategy."""
        config = self.strategy_configs.get(strategy, self.strategy_configs[RetryStrategy.STANDARD]).copy()
        
        # Adjust based on context
        if context.deadline:
            time_remaining = (context.deadline - datetime.now()).total_seconds()
            if time_remaining < config['max_delay'] * config['max_retries']:
                # Reduce delays to fit within deadline
                config['max_delay'] = min(config['max_delay'], time_remaining / config['max_retries'])
                config['base_delay'] = min(config['base_delay'], config['max_delay'] / 4)
        
        # Adjust for user-visible operations
        if context.user_visible:
            config['max_delay'] = min(config['max_delay'], 30.0)  # Don't make users wait too long
        
        return config
    
    def _check_resources(self, context: RetryContext) -> bool:
        """Check if system has enough resources for operation."""
        if context.operation_type in [OperationType.VIDEO_PROCESSING, OperationType.MEMORY_INTENSIVE]:
            memory = psutil.virtual_memory()
            
            # Check available memory
            if context.data_size and context.data_size > memory.available * 0.5:
                logger.warning(
                    "Insufficient memory for operation",
                    operation_id=context.operation_id,
                    required=context.data_size,
                    available=memory.available
                )
                return False
            
            # Check memory percentage
            if memory.percent > 90:
                return False
        
        # Check CPU for compute-intensive operations
        if context.operation_type == OperationType.VIDEO_PROCESSING:
            if psutil.cpu_percent(interval=0.1) > 90:
                return False
        
        return True
    
    async def _wait_for_resources(self, context: RetryContext, max_wait: float = 60.0):
        """Wait for system resources to become available."""
        start_time = time.time()
        check_interval = 5.0
        
        logger.info(
            "Waiting for system resources",
            operation_id=context.operation_id,
            max_wait=max_wait
        )
        
        while time.time() - start_time < max_wait:
            if self._check_resources(context):
                logger.info(
                    "Resources available",
                    operation_id=context.operation_id,
                    wait_time=time.time() - start_time
                )
                return
            
            await asyncio.sleep(check_interval)
        
        logger.warning(
            "Resource wait timeout",
            operation_id=context.operation_id,
            wait_time=max_wait
        )
    
    def _should_retry(self, exception: Exception, context: RetryContext, 
                     attempt: int, config: Dict[str, Any]) -> bool:
        """Determine if operation should be retried."""
        # Never retry certain exceptions
        non_retryable = [
            ValueError,  # Bad input
            TypeError,   # Programming error
            PermissionError,  # Won't fix itself
            KeyboardInterrupt,  # User cancellation
        ]
        
        if type(exception) in non_retryable:
            return False
        
        # Check for specific error patterns
        error_message = str(exception).lower()
        
        # Don't retry authentication errors
        if any(term in error_message for term in ['unauthorized', 'forbidden', 'invalid api key']):
            return False
        
        # Don't retry content policy violations
        if 'content policy' in error_message:
            return False
        
        # API-specific handling
        if context.operation_type == OperationType.API_CALL:
            # Retry on rate limits
            if 'rate limit' in error_message:
                return True
            
            # Retry on timeouts
            if isinstance(exception, (asyncio.TimeoutError, aiohttp.ClientTimeout)):
                return True
            
            # Retry on connection errors
            if isinstance(exception, (aiohttp.ClientError, ConnectionError)):
                return True
        
        # File operation handling
        if context.operation_type == OperationType.FILE_OPERATION:
            # Retry on disk space issues (might clear up)
            if 'no space left' in error_message:
                return attempt < 2  # Only retry once
            
            # Retry on file locks
            if 'locked' in error_message or 'in use' in error_message:
                return True
        
        # Default: retry on general exceptions
        return True
    
    def _calculate_delay(self, attempt: int, config: Dict[str, Any], 
                        context: RetryContext) -> float:
        """Calculate intelligent delay before next retry."""
        # Base exponential backoff
        base_delay = config['base_delay'] * (config['backoff_factor'] ** (attempt - 1))
        
        # Cap at maximum
        delay = min(base_delay, config['max_delay'])
        
        # Add jitter
        jitter_range = delay * config['jitter']
        jitter = random.uniform(-jitter_range, jitter_range)
        delay = max(0.1, delay + jitter)  # Minimum 100ms
        
        # Adjust for operation type
        if context.operation_type == OperationType.API_CALL:
            # Check for rate limit headers in context
            if 'retry_after' in context.failure_history[-1] if context.failure_history else {}:
                delay = max(delay, context.failure_history[-1]['retry_after'])
        
        # Adjust for priority
        if context.priority >= 8:
            delay *= 0.5  # High priority gets faster retries
        elif context.priority <= 3:
            delay *= 2.0  # Low priority can wait longer
        
        # Check deadline
        if context.deadline:
            time_remaining = (context.deadline - datetime.now()).total_seconds()
            if time_remaining > 0:
                delay = min(delay, time_remaining * 0.5)  # Use at most half remaining time
        
        return delay
    
    def _record_success(self, context: RetryContext, attempts: int, total_time: float):
        """Record successful operation."""
        operation_type = context.operation_type.value
        
        if operation_type not in self.metrics:
            self.metrics[operation_type] = RetryMetrics()
        
        metrics = self.metrics[operation_type]
        metrics.total_attempts += attempts + 1
        if attempts > 0:
            metrics.successful_retries += 1
        metrics.last_updated = datetime.now()
        
        # Update success rate
        total = metrics.successful_retries + metrics.failed_retries
        if total > 0:
            metrics.success_rate = metrics.successful_retries / total
        
        # Record in history
        self.operation_history.append({
            'operation_id': context.operation_id,
            'operation_type': operation_type,
            'timestamp': datetime.now().isoformat(),
            'success': True,
            'attempts': attempts + 1,
            'total_time': total_time,
            'priority': context.priority
        })
        
        # Trim history
        if len(self.operation_history) > 1000:
            self.operation_history = self.operation_history[-500:]
    
    def _record_failure(self, context: RetryContext, exception: Exception, attempt: int):
        """Record failed operation attempt."""
        failure_info = {
            'timestamp': datetime.now().isoformat(),
            'error_type': type(exception).__name__,
            'error_message': str(exception),
            'attempt': attempt,
            'operation_id': context.operation_id
        }
        
        context.failure_history.append(failure_info)
        
        # Update metrics
        operation_type = context.operation_type.value
        if operation_type not in self.metrics:
            self.metrics[operation_type] = RetryMetrics()
        
        metrics = self.metrics[operation_type]
        metrics.total_attempts += 1
        metrics.last_updated = datetime.now()
    
    def _create_enhanced_error(self, original_error: Exception, 
                              context: RetryContext, attempts: int) -> Exception:
        """Create enhanced error with retry context."""
        error_details = {
            'operation_id': context.operation_id,
            'operation_type': context.operation_type.value,
            'attempts': attempts,
            'priority': context.priority,
            'user_visible': context.user_visible,
            'failure_history': context.failure_history,
            'resource_usage': context.resource_usage,
            'suggested_action': self._suggest_recovery_action(original_error, context)
        }
        
        enhanced_msg = (
            f"{str(original_error)}\n"
            f"Operation '{context.operation_id}' failed after {attempts} attempts.\n"
            f"Suggested action: {error_details['suggested_action']}"
        )
        
        # Create enhanced exception
        enhanced_error = type(original_error)(enhanced_msg)
        enhanced_error.retry_context = error_details
        enhanced_error.__cause__ = original_error
        
        return enhanced_error
    
    def _suggest_recovery_action(self, error: Exception, context: RetryContext) -> str:
        """Suggest recovery action based on error and context."""
        error_msg = str(error).lower()
        
        # API errors
        if 'rate limit' in error_msg:
            return "Wait a few minutes and try again, or upgrade your API plan"
        
        if 'api key' in error_msg or 'unauthorized' in error_msg:
            return "Check your API key configuration in settings"
        
        if 'timeout' in error_msg:
            return "Check your internet connection or try again later"
        
        # Resource errors
        if 'memory' in error_msg or 'out of memory' in error_msg:
            return "Close other applications or try processing smaller files"
        
        if 'disk space' in error_msg or 'no space' in error_msg:
            return "Free up disk space or change the output directory"
        
        if 'permission' in error_msg:
            return "Check file permissions or run as administrator"
        
        # File errors
        if 'file not found' in error_msg:
            return "Ensure the file exists and the path is correct"
        
        if 'corrupt' in error_msg:
            return "The file may be corrupted. Try re-uploading or regenerating it"
        
        # Video processing
        if context.operation_type == OperationType.VIDEO_PROCESSING:
            if 'codec' in error_msg:
                return "The video format may not be supported. Try converting to MP4"
            return "Try processing a shorter video or reducing the resolution"
        
        # Default
        return "Try again in a few moments. If the problem persists, contact support"
    
    def get_metrics_summary(self) -> Dict[str, Any]:
        """Get summary of retry metrics."""
        summary = {
            'overall_success_rate': 0.0,
            'total_operations': len(self.operation_history),
            'by_type': {}
        }
        
        total_successful = 0
        total_attempts = 0
        
        for op_type, metrics in self.metrics.items():
            summary['by_type'][op_type] = {
                'total_attempts': metrics.total_attempts,
                'successful_retries': metrics.successful_retries,
                'failed_retries': metrics.failed_retries,
                'success_rate': metrics.success_rate,
                'last_updated': metrics.last_updated.isoformat() if metrics.last_updated else None
            }
            
            total_successful += metrics.successful_retries
            total_attempts += metrics.successful_retries + metrics.failed_retries
        
        if total_attempts > 0:
            summary['overall_success_rate'] = total_successful / total_attempts
        
        # Recent performance
        recent_ops = self.operation_history[-100:]
        recent_successes = sum(1 for op in recent_ops if op.get('success', False))
        summary['recent_success_rate'] = recent_successes / len(recent_ops) if recent_ops else 0
        
        return summary
    
    def clear_metrics(self):
        """Clear all metrics and history."""
        self.metrics.clear()
        self.operation_history.clear()
        logger.info("Retry metrics cleared")


# Convenience decorator
def retry_with_context(operation_type: OperationType, 
                      priority: int = 5,
                      user_visible: bool = True):
    """
    Decorator for automatic retry with context.
    
    Args:
        operation_type: Type of operation
        priority: Operation priority (1-10)
        user_visible: Whether errors are shown to users
    """
    def decorator(func: Callable) -> Callable:
        retry_manager = IntelligentRetryManager()
        
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            # Generate operation ID
            func_str = f"{func.__module__}.{func.__name__}"
            args_str = str(args)[:100] + str(kwargs)[:100]
            operation_id = hashlib.md5(f"{func_str}{args_str}{time.time()}".encode()).hexdigest()[:8]
            
            # Create context
            context = RetryContext(
                operation_id=operation_id,
                operation_type=operation_type,
                resource_usage={
                    'cpu': psutil.cpu_percent(interval=0.1),
                    'memory': psutil.virtual_memory().percent
                },
                failure_history=[],
                priority=priority,
                user_visible=user_visible
            )
            
            return await retry_manager.execute_with_retry(func, context, *args, **kwargs)
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            return asyncio.run(async_wrapper(*args, **kwargs))
        
        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper
    
    return decorator


# Global instance for convenience
default_retry_manager = IntelligentRetryManager()