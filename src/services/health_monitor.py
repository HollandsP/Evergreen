"""
Service Health Monitor

Provides comprehensive health monitoring and metrics collection
for all video generation services.
"""

import time
import asyncio
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from collections import defaultdict, deque
from enum import Enum

import structlog

logger = structlog.get_logger()


class ServiceStatus(Enum):
    """Service status levels."""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


@dataclass
class HealthMetric:
    """Individual health metric."""
    name: str
    value: float
    unit: str
    timestamp: float
    threshold_warning: Optional[float] = None
    threshold_critical: Optional[float] = None


@dataclass
class ServiceHealth:
    """Health status for a service."""
    service_name: str
    status: ServiceStatus
    metrics: List[HealthMetric] = field(default_factory=list)
    last_check: float = 0.0
    error_message: Optional[str] = None
    uptime_seconds: float = 0.0


class ServiceHealthMonitor:
    """
    Monitors health of all video generation services with metrics collection
    and alerting capabilities.
    """
    
    def __init__(self, history_size: int = 100):
        """
        Initialize health monitor.
        
        Args:
            history_size: Number of health check results to keep in history
        """
        self.history_size = history_size
        self.start_time = time.time()
        
        # Service health status
        self.service_health: Dict[str, ServiceHealth] = {}
        
        # Metrics history
        self.metrics_history: Dict[str, deque] = defaultdict(
            lambda: deque(maxlen=history_size)
        )
        
        # Failure tracking
        self.failure_counts: Dict[str, int] = defaultdict(int)
        self.failure_history: Dict[str, deque] = defaultdict(
            lambda: deque(maxlen=history_size)
        )
        
        # Performance tracking
        self.response_times: Dict[str, deque] = defaultdict(
            lambda: deque(maxlen=50)
        )
        
        logger.info(
            "Service health monitor initialized",
            history_size=history_size
        )
    
    async def check_service_health(self, service_name: str, 
                                 health_check_func: callable) -> ServiceHealth:
        """
        Check health of a specific service.
        
        Args:
            service_name: Name of service to check
            health_check_func: Function to call for health check
            
        Returns:
            Service health status
        """
        start_time = time.time()
        
        try:
            # Execute health check
            health_data = await self._execute_health_check(health_check_func)
            response_time = time.time() - start_time
            
            # Record response time
            self.response_times[service_name].append(response_time)
            
            # Parse health check result
            status = self._parse_health_status(health_data)
            metrics = self._extract_metrics(health_data, service_name)
            
            # Create health record
            health = ServiceHealth(
                service_name=service_name,
                status=status,
                metrics=metrics,
                last_check=time.time(),
                uptime_seconds=time.time() - self.start_time
            )
            
            # Update service health
            self.service_health[service_name] = health
            
            # Record metrics history
            for metric in metrics:
                self.metrics_history[f"{service_name}_{metric.name}"].append(metric)
            
            # Reset failure count on success
            if status != ServiceStatus.UNHEALTHY:
                self.failure_counts[service_name] = 0
            
            logger.debug(
                "Service health check completed",
                service_name=service_name,
                status=status.value,
                response_time_ms=round(response_time * 1000, 1)
            )
            
            return health
            
        except Exception as e:
            # Record failure
            self._record_failure(service_name, str(e))
            
            response_time = time.time() - start_time
            self.response_times[service_name].append(response_time)
            
            # Create unhealthy status
            health = ServiceHealth(
                service_name=service_name,
                status=ServiceStatus.UNHEALTHY,
                last_check=time.time(),
                error_message=str(e),
                uptime_seconds=time.time() - self.start_time
            )
            
            self.service_health[service_name] = health
            
            logger.warning(
                "Service health check failed",
                service_name=service_name,
                error=str(e),
                failure_count=self.failure_counts[service_name]
            )
            
            return health
    
    async def _execute_health_check(self, health_check_func: callable) -> Dict[str, Any]:
        """Execute health check function with timeout."""
        if asyncio.iscoroutinefunction(health_check_func):
            # Async function
            return await asyncio.wait_for(health_check_func(), timeout=10.0)
        else:
            # Sync function - run in executor
            loop = asyncio.get_event_loop()
            return await asyncio.wait_for(
                loop.run_in_executor(None, health_check_func),
                timeout=10.0
            )
    
    def _parse_health_status(self, health_data: Dict[str, Any]) -> ServiceStatus:
        """Parse health status from health check data."""
        status_str = health_data.get('status', 'unknown').lower()
        
        status_map = {
            'healthy': ServiceStatus.HEALTHY,
            'degraded': ServiceStatus.DEGRADED,
            'unhealthy': ServiceStatus.UNHEALTHY,
            'unknown': ServiceStatus.UNKNOWN
        }
        
        return status_map.get(status_str, ServiceStatus.UNKNOWN)
    
    def _extract_metrics(self, health_data: Dict[str, Any], 
                        service_name: str) -> List[HealthMetric]:
        """Extract metrics from health check data."""
        metrics = []
        timestamp = time.time()
        
        # Extract common metrics
        if 'response_time_ms' in health_data:
            metrics.append(HealthMetric(
                name='response_time',
                value=health_data['response_time_ms'],
                unit='ms',
                timestamp=timestamp,
                threshold_warning=100.0,
                threshold_critical=500.0
            ))
        
        if 'memory_usage_mb' in health_data:
            metrics.append(HealthMetric(
                name='memory_usage',
                value=health_data['memory_usage_mb'],
                unit='MB',
                timestamp=timestamp,
                threshold_warning=1024.0,
                threshold_critical=2048.0
            ))
        
        if 'active_operations' in health_data:
            metrics.append(HealthMetric(
                name='active_operations',
                value=health_data['active_operations'],
                unit='count',
                timestamp=timestamp,
                threshold_warning=5.0,
                threshold_critical=10.0
            ))
        
        if 'error_rate' in health_data:
            metrics.append(HealthMetric(
                name='error_rate',
                value=health_data['error_rate'],
                unit='%',
                timestamp=timestamp,
                threshold_warning=5.0,
                threshold_critical=15.0
            ))
        
        return metrics
    
    def _record_failure(self, service_name: str, error_message: str):
        """Record service failure."""
        self.failure_counts[service_name] += 1
        
        failure_record = {
            'timestamp': time.time(),
            'error': error_message,
            'count': self.failure_counts[service_name]
        }
        
        self.failure_history[service_name].append(failure_record)
        
        logger.error(
            "Service failure recorded",
            service_name=service_name,
            failure_count=self.failure_counts[service_name],
            error=error_message
        )
    
    def record_failure(self, service_name: str, error_message: str):
        """Public method to record external failures."""
        self._record_failure(service_name, error_message)
    
    def get_service_health(self, service_name: str) -> Optional[ServiceHealth]:
        """Get health status for a specific service."""
        return self.service_health.get(service_name)
    
    def get_all_service_health(self) -> Dict[str, ServiceHealth]:
        """Get health status for all services."""
        return self.service_health.copy()
    
    def get_system_health_summary(self) -> Dict[str, Any]:
        """Get overall system health summary."""
        if not self.service_health:
            return {
                'overall_status': ServiceStatus.UNKNOWN.value,
                'services_count': 0,
                'healthy_count': 0,
                'degraded_count': 0,
                'unhealthy_count': 0
            }
        
        status_counts = {
            ServiceStatus.HEALTHY: 0,
            ServiceStatus.DEGRADED: 0,
            ServiceStatus.UNHEALTHY: 0,
            ServiceStatus.UNKNOWN: 0
        }
        
        for health in self.service_health.values():
            status_counts[health.status] += 1
        
        # Determine overall status
        if status_counts[ServiceStatus.UNHEALTHY] > 0:
            overall_status = ServiceStatus.UNHEALTHY
        elif status_counts[ServiceStatus.DEGRADED] > 0:
            overall_status = ServiceStatus.DEGRADED
        elif status_counts[ServiceStatus.HEALTHY] > 0:
            overall_status = ServiceStatus.HEALTHY
        else:
            overall_status = ServiceStatus.UNKNOWN
        
        return {
            'overall_status': overall_status.value,
            'services_count': len(self.service_health),
            'healthy_count': status_counts[ServiceStatus.HEALTHY],
            'degraded_count': status_counts[ServiceStatus.DEGRADED],
            'unhealthy_count': status_counts[ServiceStatus.UNHEALTHY],
            'unknown_count': status_counts[ServiceStatus.UNKNOWN],
            'total_failures': sum(self.failure_counts.values()),
            'uptime_seconds': time.time() - self.start_time
        }
    
    def get_service_metrics(self, service_name: str, 
                           metric_name: str) -> List[HealthMetric]:
        """Get metric history for a service."""
        key = f"{service_name}_{metric_name}"
        return list(self.metrics_history.get(key, []))
    
    def get_service_response_times(self, service_name: str) -> List[float]:
        """Get response time history for a service."""
        return list(self.response_times.get(service_name, []))
    
    def get_service_failures(self, service_name: str) -> List[Dict[str, Any]]:
        """Get failure history for a service."""
        return list(self.failure_history.get(service_name, []))
    
    def calculate_service_availability(self, service_name: str, 
                                     time_window_seconds: int = 3600) -> float:
        """
        Calculate service availability percentage over time window.
        
        Args:
            service_name: Name of service
            time_window_seconds: Time window to calculate over (default: 1 hour)
            
        Returns:
            Availability percentage (0-100)
        """
        cutoff_time = time.time() - time_window_seconds
        
        # Get failures in time window
        failures = self.failure_history.get(service_name, [])
        recent_failures = [
            f for f in failures if f['timestamp'] > cutoff_time
        ]
        
        # Estimate total checks in time window
        # Assuming health checks every 30 seconds
        expected_checks = time_window_seconds // 30
        failure_count = len(recent_failures)
        
        if expected_checks == 0:
            return 100.0
        
        availability = ((expected_checks - failure_count) / expected_checks) * 100
        return max(0.0, min(100.0, availability))
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get performance statistics across all services."""
        stats = {}
        
        for service_name, response_times in self.response_times.items():
            if response_times:
                times = list(response_times)
                stats[service_name] = {
                    'avg_response_time_ms': round(sum(times) * 1000 / len(times), 2),
                    'min_response_time_ms': round(min(times) * 1000, 2),
                    'max_response_time_ms': round(max(times) * 1000, 2),
                    'sample_count': len(times),
                    'availability_1h': self.calculate_service_availability(service_name, 3600),
                    'failure_count': self.failure_counts.get(service_name, 0)
                }
        
        return stats
    
    def clear_metrics(self, service_name: Optional[str] = None):
        """Clear metrics history for a service or all services."""
        if service_name:
            # Clear specific service
            keys_to_clear = [k for k in self.metrics_history.keys() if k.startswith(f"{service_name}_")]
            for key in keys_to_clear:
                self.metrics_history[key].clear()
            
            self.response_times.pop(service_name, None)
            self.failure_history.pop(service_name, None)
            self.failure_counts.pop(service_name, None)
            
            logger.info(f"Cleared metrics for service: {service_name}")
        else:
            # Clear all metrics
            self.metrics_history.clear()
            self.response_times.clear()
            self.failure_history.clear()
            self.failure_counts.clear()
            
            logger.info("Cleared all metrics")
    
    def export_health_data(self) -> Dict[str, Any]:
        """Export all health data for external monitoring."""
        return {
            'timestamp': time.time(),
            'monitor_uptime_seconds': time.time() - self.start_time,
            'system_health': self.get_system_health_summary(),
            'service_health': {
                name: {
                    'status': health.status.value,
                    'last_check': health.last_check,
                    'error_message': health.error_message,
                    'metrics': [
                        {
                            'name': m.name,
                            'value': m.value,
                            'unit': m.unit,
                            'timestamp': m.timestamp
                        }
                        for m in health.metrics
                    ]
                }
                for name, health in self.service_health.items()
            },
            'performance_stats': self.get_performance_stats(),
            'total_services': len(self.service_health),
            'total_metrics_collected': sum(len(h) for h in self.metrics_history.values())
        }