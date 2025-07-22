"""
Circuit Breaker Pattern Implementation

Provides circuit breaker functionality to prevent cascading failures
when external services are unavailable.
"""

import asyncio
import time
from enum import Enum
from typing import Any, Callable, Optional, Type, Union

import structlog

logger = structlog.get_logger()


class CircuitBreakerState(Enum):
    """Circuit breaker states."""
    CLOSED = "closed"      # Normal operation
    OPEN = "open"          # Circuit is open, rejecting calls  
    HALF_OPEN = "half_open"  # Testing if service has recovered


class CircuitBreakerError(Exception):
    """Raised when circuit breaker is open."""
    pass


class CircuitBreaker:
    """
    Circuit breaker implementation to handle external service failures.
    
    The circuit breaker has three states:
    - CLOSED: Normal operation, all calls pass through
    - OPEN: Service is failing, all calls are rejected immediately
    - HALF_OPEN: Testing mode, limited calls allowed to test recovery
    """
    
    def __init__(self, failure_threshold: int = 5,
                 recovery_timeout: float = 60.0,
                 expected_exception: Type[Exception] = Exception,
                 half_open_max_calls: int = 3):
        """
        Initialize circuit breaker.
        
        Args:
            failure_threshold: Number of failures before opening circuit
            recovery_timeout: Seconds to wait before entering half-open state
            expected_exception: Exception type(s) that should trigger the circuit
            half_open_max_calls: Max calls allowed in half-open state
        """
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exception = expected_exception
        self.half_open_max_calls = half_open_max_calls
        
        # State tracking
        self.state = CircuitBreakerState.CLOSED
        self.failure_count = 0
        self.last_failure_time = 0.0
        self.half_open_calls = 0
        
        # Statistics
        self.total_calls = 0
        self.total_failures = 0
        self.total_successes = 0
        
        logger.info(
            "Circuit breaker initialized",
            failure_threshold=failure_threshold,
            recovery_timeout=recovery_timeout
        )
    
    async def call(self, func: Callable, *args, **kwargs) -> Any:
        """
        Execute function with circuit breaker protection.
        
        Args:
            func: Function to execute (can be async or sync)
            *args: Function arguments
            **kwargs: Function keyword arguments
            
        Returns:
            Function result
            
        Raises:
            CircuitBreakerError: When circuit is open
            Original exception: When function fails in closed/half-open state
        """
        self.total_calls += 1
        
        # Check if circuit should be opened
        if self.state == CircuitBreakerState.OPEN:
            if time.time() - self.last_failure_time > self.recovery_timeout:
                self._transition_to_half_open()
            else:
                self._record_rejected_call()
                raise CircuitBreakerError("Circuit breaker is open")
        
        # Check half-open state limits
        if self.state == CircuitBreakerState.HALF_OPEN:
            if self.half_open_calls >= self.half_open_max_calls:
                self._record_rejected_call()
                raise CircuitBreakerError("Circuit breaker half-open limit exceeded")
            self.half_open_calls += 1
        
        try:
            # Execute the function
            if asyncio.iscoroutinefunction(func):
                result = await func(*args, **kwargs)
            else:
                result = func(*args, **kwargs)
            
            # Success - reset failure count and close circuit if needed
            self._record_success()
            return result
            
        except self.expected_exception as e:
            # Expected failure - record and potentially open circuit
            self._record_failure()
            raise e
        except Exception as e:
            # Unexpected exception - let it pass through without affecting circuit
            logger.warning(
                "Unexpected exception in circuit breaker",
                exception_type=type(e).__name__,
                error=str(e)
            )
            raise e
    
    def _record_success(self):
        """Record successful call."""
        self.total_successes += 1
        
        if self.state == CircuitBreakerState.HALF_OPEN:
            # Successful call in half-open state
            logger.info("Circuit breaker test call succeeded, closing circuit")
            self._transition_to_closed()
        elif self.state == CircuitBreakerState.CLOSED:
            # Reset failure count on success
            self.failure_count = 0
    
    def _record_failure(self):
        """Record failed call."""
        self.total_failures += 1
        self.failure_count += 1
        self.last_failure_time = time.time()
        
        logger.warning(
            \"Circuit breaker recorded failure\",\n            failure_count=self.failure_count,\n            threshold=self.failure_threshold,\n            state=self.state.value\n        )\n        \n        if self.state == CircuitBreakerState.HALF_OPEN:\n            # Failure in half-open state - go back to open\n            logger.warning(\"Circuit breaker test failed, reopening circuit\")\n            self._transition_to_open()\n        elif self.failure_count >= self.failure_threshold:\n            # Reached failure threshold - open circuit\n            logger.error(\n                \"Circuit breaker failure threshold reached, opening circuit\",\n                failure_count=self.failure_count,\n                threshold=self.failure_threshold\n            )\n            self._transition_to_open()\n    \n    def _record_rejected_call(self):\n        \"\"\"Record call rejected due to open circuit.\"\"\"\n        logger.debug(\"Circuit breaker rejected call\", state=self.state.value)\n    \n    def _transition_to_closed(self):\n        \"\"\"Transition to closed state.\"\"\"\n        self.state = CircuitBreakerState.CLOSED\n        self.failure_count = 0\n        self.half_open_calls = 0\n        \n        logger.info(\"Circuit breaker transitioned to CLOSED\")\n    \n    def _transition_to_open(self):\n        \"\"\"Transition to open state.\"\"\"\n        self.state = CircuitBreakerState.OPEN\n        self.half_open_calls = 0\n        \n        logger.warning(\n            \"Circuit breaker transitioned to OPEN\",\n            recovery_timeout=self.recovery_timeout\n        )\n    \n    def _transition_to_half_open(self):\n        \"\"\"Transition to half-open state.\"\"\"\n        self.state = CircuitBreakerState.HALF_OPEN\n        self.half_open_calls = 0\n        \n        logger.info(\n            \"Circuit breaker transitioned to HALF_OPEN\",\n            max_calls=self.half_open_max_calls\n        )\n    \n    def reset(self):\n        \"\"\"Manually reset circuit breaker to closed state.\"\"\"\n        logger.info(\"Circuit breaker manually reset\")\n        self._transition_to_closed()\n    \n    def force_open(self):\n        \"\"\"Manually force circuit breaker to open state.\"\"\"\n        logger.warning(\"Circuit breaker manually opened\")\n        self.last_failure_time = time.time()\n        self._transition_to_open()\n    \n    def get_stats(self) -> dict:\n        \"\"\"Get circuit breaker statistics.\"\"\"\n        success_rate = (\n            (self.total_successes / self.total_calls * 100) \n            if self.total_calls > 0 else 0\n        )\n        \n        return {\n            'state': self.state.value,\n            'failure_count': self.failure_count,\n            'failure_threshold': self.failure_threshold,\n            'total_calls': self.total_calls,\n            'total_successes': self.total_successes,\n            'total_failures': self.total_failures,\n            'success_rate': round(success_rate, 2),\n            'last_failure_time': self.last_failure_time,\n            'half_open_calls': self.half_open_calls,\n            'recovery_timeout': self.recovery_timeout\n        }"