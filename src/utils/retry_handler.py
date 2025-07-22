"""
Retry Handler with Exponential Backoff

Provides robust retry mechanisms with exponential backoff, jitter,
and configurable retry conditions.
"""

import asyncio
import random
import time
from typing import Any, Callable, Optional, Type, Union, List
from functools import wraps

import structlog

logger = structlog.get_logger()


class RetryExhausted(Exception):
    """Raised when all retry attempts are exhausted."""
    
    def __init__(self, message: str, last_exception: Exception, attempt_count: int):
        super().__init__(message)
        self.last_exception = last_exception
        self.attempt_count = attempt_count


class RetryHandler:
    """
    Retry handler with exponential backoff and jitter.
    
    Provides configurable retry logic with:
    - Exponential backoff
    - Random jitter to prevent thundering herd
    - Configurable retry conditions
    - Support for async and sync functions
    """
    
    def __init__(self, max_retries: int = 3,
                 base_delay: float = 1.0,
                 max_delay: float = 60.0,
                 backoff_factor: float = 2.0,
                 jitter: bool = True,
                 retry_exceptions: Optional[List[Type[Exception]]] = None):
        """
        Initialize retry handler.
        
        Args:
            max_retries: Maximum number of retry attempts
            base_delay: Base delay between retries in seconds
            max_delay: Maximum delay between retries in seconds
            backoff_factor: Multiplier for exponential backoff
            jitter: Whether to add random jitter to delays
            retry_exceptions: List of exceptions that should trigger retries
        """
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.backoff_factor = backoff_factor
        self.jitter = jitter
        self.retry_exceptions = retry_exceptions or [Exception]
        
        logger.info(
            "Retry handler initialized",
            max_retries=max_retries,
            base_delay=base_delay,
            backoff_factor=backoff_factor
        )
    
    async def execute_with_retry(self, func: Callable, *args, 
                               max_retries: Optional[int] = None,
                               backoff_factor: Optional[float] = None,
                               **kwargs) -> Any:
        """
        Execute function with retry logic.
        
        Args:
            func: Function to execute (can be async or sync)
            *args: Function arguments
            max_retries: Override default max retries for this call
            backoff_factor: Override default backoff factor for this call
            **kwargs: Function keyword arguments
            
        Returns:
            Function result
            
        Raises:
            RetryExhausted: When all retry attempts are exhausted
        """
        max_retries = max_retries if max_retries is not None else self.max_retries
        backoff_factor = backoff_factor if backoff_factor is not None else self.backoff_factor
        
        last_exception = None
        
        for attempt in range(max_retries + 1):  # +1 because first attempt is not a retry
            try:
                logger.debug(
                    "Executing function with retry",
                    function=func.__name__,
                    attempt=attempt + 1,
                    max_attempts=max_retries + 1
                )
                
                # Execute the function
                if asyncio.iscoroutinefunction(func):
                    result = await func(*args, **kwargs)
                else:
                    result = func(*args, **kwargs)
                
                if attempt > 0:
                    logger.info(
                        "Function succeeded after retries",
                        function=func.__name__,
                        attempts=attempt + 1
                    )
                
                return result
                
            except Exception as e:
                last_exception = e
                
                # Check if this exception should trigger a retry
                if not self._should_retry(e):
                    logger.info(
                        "Exception not retryable, raising immediately",
                        function=func.__name__,
                        exception=type(e).__name__,
                        error=str(e)
                    )
                    raise e
                
                # If this is the last attempt, don't wait - just fail
                if attempt >= max_retries:
                    break
                
                # Calculate delay for next attempt
                delay = self._calculate_delay(attempt, backoff_factor)
                
                logger.warning(
                    "Function failed, retrying",
                    function=func.__name__,
                    attempt=attempt + 1,
                    max_attempts=max_retries + 1,
                    exception=type(e).__name__,
                    error=str(e),
                    retry_delay=delay
                )
                
                # Wait before retry
                await asyncio.sleep(delay)
        
        # All retries exhausted
        error_msg = f"Function {func.__name__} failed after {max_retries + 1} attempts"
        logger.error(
            "All retry attempts exhausted",
            function=func.__name__,
            attempts=max_retries + 1,
            last_error=str(last_exception)
        )
        
        raise RetryExhausted(error_msg, last_exception, max_retries + 1)
    
    def _should_retry(self, exception: Exception) -> bool:
        """
        Determine if an exception should trigger a retry.
        
        Args:
            exception: Exception that occurred
            
        Returns:
            True if should retry, False otherwise
        """
        for retry_exception in self.retry_exceptions:
            if isinstance(exception, retry_exception):
                return True
        return False
    
    def _calculate_delay(self, attempt: int, backoff_factor: float) -> float:
        """
        Calculate delay before next retry attempt.
        
        Args:
            attempt: Current attempt number (0-based)
            backoff_factor: Backoff multiplier
            
        Returns:
            Delay in seconds
        """
        # Exponential backoff
        delay = self.base_delay * (backoff_factor ** attempt)
        
        # Cap at maximum delay
        delay = min(delay, self.max_delay)
        
        # Add jitter if enabled
        if self.jitter:
            # Add up to 25% jitter
            jitter_amount = delay * 0.25
            jitter = random.uniform(-jitter_amount, jitter_amount)
            delay = max(0, delay + jitter)
        
        return delay
    
    def retry_decorator(self, max_retries: Optional[int] = None,
                       backoff_factor: Optional[float] = None):
        """
        Decorator for automatic retry functionality.
        
        Args:
            max_retries: Override default max retries
            backoff_factor: Override default backoff factor
            
        Returns:
            Decorated function
        """
        def decorator(func: Callable) -> Callable:
            @wraps(func)
            async def async_wrapper(*args, **kwargs):
                return await self.execute_with_retry(
                    func, *args, 
                    max_retries=max_retries,
                    backoff_factor=backoff_factor,
                    **kwargs
                )
            
            @wraps(func)
            def sync_wrapper(*args, **kwargs):
                # For sync functions, we need to run in event loop
                if asyncio.iscoroutinefunction(func):
                    return async_wrapper(*args, **kwargs)
                else:
                    # Create async wrapper for sync function
                    async def async_func(*a, **kw):
                        return func(*a, **kw)
                    
                    # Run in current event loop if available
                    try:
                        loop = asyncio.get_event_loop()
                        if loop.is_running():
                            # Can't use run() in running loop, create task
                            return asyncio.create_task(
                                async_wrapper(*args, **kwargs)
                            )
                        else:
                            return loop.run_until_complete(
                                async_wrapper(*args, **kwargs)
                            )
                    except RuntimeError:
                        # No event loop, create new one
                        return asyncio.run(async_wrapper(*args, **kwargs))
            
            if asyncio.iscoroutinefunction(func):
                return async_wrapper
            else:
                return sync_wrapper
        
        return decorator


# Convenience decorators for common retry patterns
def retry_on_exception(exceptions: List[Type[Exception]], max_retries: int = 3,
                      backoff_factor: float = 2.0, base_delay: float = 1.0):
    """
    Convenience decorator for retrying on specific exceptions.
    
    Args:
        exceptions: List of exception types to retry on
        max_retries: Maximum retry attempts
        backoff_factor: Exponential backoff factor
        base_delay: Base delay between retries
    """
    handler = RetryHandler(
        max_retries=max_retries,
        backoff_factor=backoff_factor,
        base_delay=base_delay,
        retry_exceptions=exceptions
    )
    return handler.retry_decorator()


def retry_on_network_error(max_retries: int = 3, backoff_factor: float = 2.0):
    """
    Convenience decorator for retrying on network-related errors.
    
    Args:
        max_retries: Maximum retry attempts
        backoff_factor: Exponential backoff factor
    """
    import requests
    from urllib3.exceptions import ConnectionError as URLConnectionError
    
    network_exceptions = [
        requests.exceptions.ConnectionError,
        requests.exceptions.Timeout,
        requests.exceptions.RequestException,
        URLConnectionError,
        OSError,  # For general network issues
    ]
    
    return retry_on_exception(
        network_exceptions, 
        max_retries=max_retries,
        backoff_factor=backoff_factor
    )