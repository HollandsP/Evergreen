"""
Error Context Logger with Correlation IDs and Actionable Insights

Provides comprehensive error tracking with:
- Correlation IDs for request tracing
- Detailed context capture
- Error pattern analysis
- Actionable recovery suggestions
- Integration with monitoring systems
"""

import asyncio
import json
import traceback
import uuid
import sys
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Set, Union, Callable
from dataclasses import dataclass, asdict
from collections import defaultdict, deque
from enum import Enum
import inspect
import os

import structlog
from contextvars import ContextVar

# Context variable for correlation ID
correlation_id_var: ContextVar[str] = ContextVar('correlation_id', default=None)

logger = structlog.get_logger()


class ErrorSeverity(Enum):
    """Error severity levels."""
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"
    FATAL = "fatal"


class ErrorCategory(Enum):
    """Categories of errors for better organization."""
    API_ERROR = "api_error"
    DATABASE_ERROR = "database_error"
    FILE_ERROR = "file_error"
    NETWORK_ERROR = "network_error"
    VALIDATION_ERROR = "validation_error"
    PROCESSING_ERROR = "processing_error"
    RESOURCE_ERROR = "resource_error"
    AUTHENTICATION_ERROR = "authentication_error"
    PERMISSION_ERROR = "permission_error"
    UNKNOWN_ERROR = "unknown_error"


@dataclass
class ErrorContext:
    """Comprehensive error context information."""
    error_id: str
    correlation_id: str
    timestamp: datetime
    severity: ErrorSeverity
    category: ErrorCategory
    error_type: str
    error_message: str
    stack_trace: str
    
    # Context information
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    request_id: Optional[str] = None
    operation: Optional[str] = None
    
    # Technical details
    file_path: Optional[str] = None
    line_number: Optional[int] = None
    function_name: Optional[str] = None
    module_name: Optional[str] = None
    
    # Additional context
    input_data: Optional[Dict[str, Any]] = None
    system_state: Optional[Dict[str, Any]] = None
    related_errors: Optional[List[str]] = None
    recovery_attempted: bool = False
    recovery_successful: bool = False
    
    # User impact
    user_visible: bool = True
    user_message: Optional[str] = None
    suggested_action: Optional[str] = None
    
    # Metadata
    tags: Optional[List[str]] = None
    custom_data: Optional[Dict[str, Any]] = None


class ErrorPattern:
    """Tracks error patterns for intelligent analysis."""
    
    def __init__(self, pattern_id: str, error_type: str):
        self.pattern_id = pattern_id
        self.error_type = error_type
        self.occurrences: List[ErrorContext] = []
        self.first_seen = datetime.now()
        self.last_seen = datetime.now()
        self.count = 0
        self.recovery_success_rate = 0.0
        
    def add_occurrence(self, error: ErrorContext):
        """Add new error occurrence to pattern."""
        self.occurrences.append(error)
        self.count += 1
        self.last_seen = datetime.now()
        
        # Keep only recent occurrences
        if len(self.occurrences) > 100:
            self.occurrences = self.occurrences[-50:]
        
        # Calculate recovery success rate
        recovered = sum(1 for e in self.occurrences if e.recovery_successful)
        attempted = sum(1 for e in self.occurrences if e.recovery_attempted)
        if attempted > 0:
            self.recovery_success_rate = recovered / attempted


class ErrorContextLogger:
    """
    Advanced error logging with context tracking and pattern analysis.
    
    Features:
    - Correlation ID tracking across requests
    - Detailed error context capture
    - Pattern detection and analysis
    - Recovery suggestions
    - Integration with monitoring
    """
    
    def __init__(self, 
                 app_name: str = "evergreen",
                 environment: str = "development",
                 max_history: int = 10000):
        """
        Initialize error context logger.
        
        Args:
            app_name: Application name for logging
            environment: Environment (development, staging, production)
            max_history: Maximum error history to maintain
        """
        self.app_name = app_name
        self.environment = environment
        self.max_history = max_history
        
        # Error tracking
        self.error_history: deque = deque(maxlen=max_history)
        self.error_patterns: Dict[str, ErrorPattern] = {}
        self.correlation_chains: Dict[str, List[ErrorContext]] = defaultdict(list)
        
        # Statistics
        self.error_counts: Dict[ErrorCategory, int] = defaultdict(int)
        self.severity_counts: Dict[ErrorSeverity, int] = defaultdict(int)
        self.recovery_stats: Dict[str, Dict[str, int]] = defaultdict(lambda: {"attempted": 0, "successful": 0})
        
        logger.info(
            "Error context logger initialized",
            app_name=app_name,
            environment=environment
        )
    
    def set_correlation_id(self, correlation_id: Optional[str] = None) -> str:
        """Set correlation ID for current context."""
        if correlation_id is None:
            correlation_id = str(uuid.uuid4())
        correlation_id_var.set(correlation_id)
        return correlation_id
    
    def get_correlation_id(self) -> str:
        """Get current correlation ID or create new one."""
        correlation_id = correlation_id_var.get()
        if correlation_id is None:
            correlation_id = self.set_correlation_id()
        return correlation_id
    
    async def log_error(self,
                       exception: Exception,
                       severity: ErrorSeverity = ErrorSeverity.ERROR,
                       category: Optional[ErrorCategory] = None,
                       operation: Optional[str] = None,
                       user_id: Optional[str] = None,
                       session_id: Optional[str] = None,
                       input_data: Optional[Dict[str, Any]] = None,
                       user_visible: bool = True,
                       tags: Optional[List[str]] = None,
                       custom_data: Optional[Dict[str, Any]] = None) -> ErrorContext:
        """
        Log error with comprehensive context.
        
        Args:
            exception: The exception to log
            severity: Error severity level
            category: Error category for grouping
            operation: Operation being performed
            user_id: User identifier
            session_id: Session identifier
            input_data: Input data that caused error
            user_visible: Whether error is shown to user
            tags: Additional tags for categorization
            custom_data: Any custom data to attach
            
        Returns:
            ErrorContext object with all details
        """
        # Get stack information
        tb = traceback.extract_tb(exception.__traceback__)
        if tb:
            last_frame = tb[-1]
            file_path = last_frame.filename
            line_number = last_frame.lineno
            function_name = last_frame.name
            module_name = os.path.basename(file_path).replace('.py', '')
        else:
            file_path = line_number = function_name = module_name = None
        
        # Determine category if not provided
        if category is None:
            category = self._categorize_error(exception)
        
        # Create error context
        error_context = ErrorContext(
            error_id=str(uuid.uuid4()),
            correlation_id=self.get_correlation_id(),
            timestamp=datetime.now(),
            severity=severity,
            category=category,
            error_type=type(exception).__name__,
            error_message=str(exception),
            stack_trace=traceback.format_exc(),
            user_id=user_id,
            session_id=session_id,
            request_id=self.get_correlation_id(),
            operation=operation,
            file_path=file_path,
            line_number=line_number,
            function_name=function_name,
            module_name=module_name,
            input_data=self._sanitize_data(input_data) if input_data else None,
            system_state=await self._capture_system_state(),
            user_visible=user_visible,
            user_message=self._generate_user_message(exception, category),
            suggested_action=self._suggest_action(exception, category),
            tags=tags,
            custom_data=custom_data
        )
        
        # Track error
        self._track_error(error_context)
        
        # Log structured error
        logger.error(
            "Error logged with context",
            error_id=error_context.error_id,
            correlation_id=error_context.correlation_id,
            severity=severity.value,
            category=category.value,
            error_type=error_context.error_type,
            operation=operation,
            user_visible=user_visible,
            **{"error_message": error_context.error_message}
        )
        
        # Analyze patterns
        self._analyze_patterns(error_context)
        
        return error_context
    
    def _categorize_error(self, exception: Exception) -> ErrorCategory:
        """Categorize error based on exception type and message."""
        error_type = type(exception).__name__
        error_msg = str(exception).lower()
        
        # API errors
        if any(term in error_msg for term in ['api', 'endpoint', 'request', 'response']):
            return ErrorCategory.API_ERROR
        
        # Database errors
        if any(term in error_msg for term in ['database', 'query', 'connection', 'postgres', 'redis']):
            return ErrorCategory.DATABASE_ERROR
        
        # File errors
        if any(term in error_msg for term in ['file', 'path', 'directory', 'disk']):
            return ErrorCategory.FILE_ERROR
        
        # Network errors
        if any(term in error_msg for term in ['network', 'timeout', 'connection', 'socket']):
            return ErrorCategory.NETWORK_ERROR
        
        # Validation errors
        if any(term in error_msg for term in ['validation', 'invalid', 'required', 'format']):
            return ErrorCategory.VALIDATION_ERROR
        
        # Authentication errors
        if any(term in error_msg for term in ['auth', 'unauthorized', 'forbidden', 'token']):
            return ErrorCategory.AUTHENTICATION_ERROR
        
        # Permission errors
        if 'permission' in error_msg or isinstance(exception, PermissionError):
            return ErrorCategory.PERMISSION_ERROR
        
        # Resource errors
        if any(term in error_msg for term in ['memory', 'cpu', 'resource', 'quota']):
            return ErrorCategory.RESOURCE_ERROR
        
        # Processing errors
        if any(term in error_msg for term in ['process', 'convert', 'transform', 'encode']):
            return ErrorCategory.PROCESSING_ERROR
        
        return ErrorCategory.UNKNOWN_ERROR
    
    def _sanitize_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Sanitize sensitive data before logging."""
        sensitive_keys = {
            'password', 'token', 'key', 'secret', 'credential',
            'api_key', 'access_token', 'refresh_token', 'auth'
        }
        
        sanitized = {}
        for key, value in data.items():
            if any(sensitive in key.lower() for sensitive in sensitive_keys):
                sanitized[key] = "[REDACTED]"
            elif isinstance(value, dict):
                sanitized[key] = self._sanitize_data(value)
            elif isinstance(value, str) and len(value) > 1000:
                sanitized[key] = f"{value[:100]}... [TRUNCATED]"
            else:
                sanitized[key] = value
        
        return sanitized
    
    async def _capture_system_state(self) -> Dict[str, Any]:
        """Capture current system state for debugging."""
        try:
            import psutil
            
            return {
                'cpu_percent': psutil.cpu_percent(interval=0.1),
                'memory_percent': psutil.virtual_memory().percent,
                'disk_usage': psutil.disk_usage('/').percent,
                'timestamp': datetime.now().isoformat()
            }
        except Exception:
            return {'error': 'Failed to capture system state'}
    
    def _generate_user_message(self, exception: Exception, category: ErrorCategory) -> str:
        """Generate user-friendly error message."""
        if category == ErrorCategory.API_ERROR:
            if 'rate limit' in str(exception).lower():
                return "We're experiencing high demand. Please try again in a few moments."
            return "We're having trouble connecting to our services. Please try again."
        
        elif category == ErrorCategory.FILE_ERROR:
            return "There was an issue with the file. Please check it and try again."
        
        elif category == ErrorCategory.NETWORK_ERROR:
            return "Connection issue detected. Please check your internet and try again."
        
        elif category == ErrorCategory.VALIDATION_ERROR:
            return "Please check your input and try again."
        
        elif category == ErrorCategory.AUTHENTICATION_ERROR:
            return "Authentication failed. Please check your credentials."
        
        elif category == ErrorCategory.PERMISSION_ERROR:
            return "You don't have permission to perform this action."
        
        elif category == ErrorCategory.RESOURCE_ERROR:
            return "System resources are limited. Please try again later."
        
        elif category == ErrorCategory.PROCESSING_ERROR:
            return "We encountered an issue processing your request. Please try again."
        
        return "An unexpected error occurred. Please try again or contact support."
    
    def _suggest_action(self, exception: Exception, category: ErrorCategory) -> str:
        """Suggest recovery action based on error."""
        error_msg = str(exception).lower()
        
        if category == ErrorCategory.API_ERROR:
            if 'rate limit' in error_msg:
                return "Wait a few minutes before retrying"
            elif 'timeout' in error_msg:
                return "Check your internet connection"
            return "Refresh the page and try again"
        
        elif category == ErrorCategory.FILE_ERROR:
            if 'not found' in error_msg:
                return "Ensure the file exists and the path is correct"
            elif 'permission' in error_msg:
                return "Check file permissions"
            elif 'space' in error_msg:
                return "Free up disk space"
            return "Try uploading the file again"
        
        elif category == ErrorCategory.NETWORK_ERROR:
            return "Check your internet connection and firewall settings"
        
        elif category == ErrorCategory.VALIDATION_ERROR:
            return "Review the error message and correct your input"
        
        elif category == ErrorCategory.AUTHENTICATION_ERROR:
            return "Sign out and sign in again"
        
        elif category == ErrorCategory.RESOURCE_ERROR:
            if 'memory' in error_msg:
                return "Close other applications or try with smaller files"
            return "Wait a few minutes for resources to become available"
        
        return "If the problem persists, contact support with error ID"
    
    def _track_error(self, error: ErrorContext):
        """Track error in internal structures."""
        # Add to history
        self.error_history.append(error)
        
        # Update counts
        self.error_counts[error.category] += 1
        self.severity_counts[error.severity] += 1
        
        # Track correlation chain
        self.correlation_chains[error.correlation_id].append(error)
        
        # Clean old correlation chains
        cutoff_time = datetime.now() - timedelta(hours=24)
        old_chains = [
            cid for cid, errors in self.correlation_chains.items()
            if all(e.timestamp < cutoff_time for e in errors)
        ]
        for cid in old_chains:
            del self.correlation_chains[cid]
    
    def _analyze_patterns(self, error: ErrorContext):
        """Analyze error patterns for insights."""
        pattern_key = f"{error.error_type}:{error.category.value}"
        
        if pattern_key not in self.error_patterns:
            self.error_patterns[pattern_key] = ErrorPattern(
                pattern_id=str(uuid.uuid4()),
                error_type=error.error_type
            )
        
        pattern = self.error_patterns[pattern_key]
        pattern.add_occurrence(error)
        
        # Check for error spike
        recent_errors = [
            e for e in pattern.occurrences
            if e.timestamp > datetime.now() - timedelta(minutes=5)
        ]
        
        if len(recent_errors) > 10:
            logger.warning(
                "Error spike detected",
                pattern_key=pattern_key,
                count=len(recent_errors),
                recovery_rate=pattern.recovery_success_rate
            )
    
    def log_recovery_attempt(self, error_id: str, successful: bool):
        """Log recovery attempt for an error."""
        # Find error in history
        for error in self.error_history:
            if error.error_id == error_id:
                error.recovery_attempted = True
                error.recovery_successful = successful
                
                # Update stats
                key = f"{error.error_type}:{error.category.value}"
                self.recovery_stats[key]["attempted"] += 1
                if successful:
                    self.recovery_stats[key]["successful"] += 1
                
                logger.info(
                    "Recovery attempt logged",
                    error_id=error_id,
                    successful=successful
                )
                break
    
    def get_error_summary(self, hours: int = 24) -> Dict[str, Any]:
        """Get summary of recent errors."""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        recent_errors = [
            e for e in self.error_history
            if e.timestamp > cutoff_time
        ]
        
        summary = {
            'total_errors': len(recent_errors),
            'by_category': defaultdict(int),
            'by_severity': defaultdict(int),
            'top_errors': [],
            'recovery_stats': {},
            'error_rate': len(recent_errors) / hours if hours > 0 else 0
        }
        
        # Count by category and severity
        for error in recent_errors:
            summary['by_category'][error.category.value] += 1
            summary['by_severity'][error.severity.value] += 1
        
        # Top error types
        error_type_counts = defaultdict(int)
        for error in recent_errors:
            error_type_counts[error.error_type] += 1
        
        summary['top_errors'] = sorted(
            error_type_counts.items(),
            key=lambda x: x[1],
            reverse=True
        )[:10]
        
        # Recovery stats
        for key, stats in self.recovery_stats.items():
            if stats['attempted'] > 0:
                summary['recovery_stats'][key] = {
                    'attempted': stats['attempted'],
                    'successful': stats['successful'],
                    'success_rate': stats['successful'] / stats['attempted']
                }
        
        return summary
    
    def get_correlation_chain(self, correlation_id: str) -> List[ErrorContext]:
        """Get all errors in a correlation chain."""
        return self.correlation_chains.get(correlation_id, [])
    
    def export_errors(self, 
                     start_time: Optional[datetime] = None,
                     end_time: Optional[datetime] = None,
                     category: Optional[ErrorCategory] = None,
                     severity: Optional[ErrorSeverity] = None) -> List[Dict[str, Any]]:
        """Export errors matching criteria."""
        errors = list(self.error_history)
        
        # Filter by time
        if start_time:
            errors = [e for e in errors if e.timestamp >= start_time]
        if end_time:
            errors = [e for e in errors if e.timestamp <= end_time]
        
        # Filter by category
        if category:
            errors = [e for e in errors if e.category == category]
        
        # Filter by severity
        if severity:
            errors = [e for e in errors if e.severity == severity]
        
        # Convert to dict
        return [asdict(e) for e in errors]
    
    def clear_old_errors(self, days: int = 7):
        """Clear errors older than specified days."""
        cutoff_time = datetime.now() - timedelta(days=days)
        
        # Filter error history
        self.error_history = deque(
            (e for e in self.error_history if e.timestamp > cutoff_time),
            maxlen=self.max_history
        )
        
        # Clean patterns
        for pattern in self.error_patterns.values():
            pattern.occurrences = [
                e for e in pattern.occurrences
                if e.timestamp > cutoff_time
            ]
        
        logger.info(
            "Old errors cleared",
            days=days,
            remaining_errors=len(self.error_history)
        )


# Global instance
error_logger = ErrorContextLogger()


# Decorator for automatic error logging
def log_errors(severity: ErrorSeverity = ErrorSeverity.ERROR,
              category: Optional[ErrorCategory] = None,
              user_visible: bool = True):
    """
    Decorator for automatic error logging with context.
    
    Args:
        severity: Default severity level
        category: Error category
        user_visible: Whether errors are shown to users
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                await error_logger.log_error(
                    exception=e,
                    severity=severity,
                    category=category,
                    operation=f"{func.__module__}.{func.__name__}",
                    user_visible=user_visible,
                    input_data={'args': str(args)[:200], 'kwargs': str(kwargs)[:200]}
                )
                raise
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                asyncio.create_task(
                    error_logger.log_error(
                        exception=e,
                        severity=severity,
                        category=category,
                        operation=f"{func.__module__}.{func.__name__}",
                        user_visible=user_visible,
                        input_data={'args': str(args)[:200], 'kwargs': str(kwargs)[:200]}
                    )
                )
                raise
        
        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper
    
    return decorator