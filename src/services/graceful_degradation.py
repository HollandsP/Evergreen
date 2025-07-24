"""
Graceful Degradation Service with Intelligent Fallbacks

Provides service degradation capabilities with:
- Automatic fallback strategies
- Quality reduction options
- Service substitution
- Feature toggling
- Performance-based adaptation
"""

import asyncio
import time
from typing import Dict, List, Optional, Any, Callable, Union, Set
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from collections import defaultdict
import json

import structlog
import psutil
from abc import ABC, abstractmethod

logger = structlog.get_logger()


class ServiceLevel(Enum):
    """Service operational levels."""
    FULL = "full"           # All features enabled
    REDUCED = "reduced"     # Some features disabled
    MINIMAL = "minimal"     # Core features only
    EMERGENCY = "emergency" # Bare minimum functionality
    OFFLINE = "offline"     # Service unavailable


class DegradationReason(Enum):
    """Reasons for service degradation."""
    HIGH_LOAD = "high_load"
    API_LIMIT = "api_limit"
    RESOURCE_CONSTRAINT = "resource_constraint"
    ERROR_RATE = "error_rate"
    DEPENDENCY_FAILURE = "dependency_failure"
    MANUAL_OVERRIDE = "manual_override"


@dataclass
class ServiceMetrics:
    """Metrics for service health monitoring."""
    response_time_ms: float = 0.0
    error_rate: float = 0.0
    throughput: float = 0.0
    resource_usage: Dict[str, float] = field(default_factory=dict)
    success_count: int = 0
    error_count: int = 0
    last_updated: datetime = field(default_factory=datetime.now)


@dataclass
class FallbackStrategy:
    """Fallback strategy configuration."""
    name: str
    target_level: ServiceLevel
    conditions: Dict[str, Any]
    actions: List[str]
    priority: int = 10
    cooldown_seconds: int = 300
    
    
class ServiceAdapter(ABC):
    """Base class for service-specific adaptation."""
    
    @abstractmethod
    async def adapt_to_level(self, level: ServiceLevel) -> bool:
        """Adapt service to specified level."""
        pass
    
    @abstractmethod
    def get_current_capabilities(self) -> Dict[str, Any]:
        """Get current service capabilities."""
        pass


class GracefulDegradationService:
    """
    Intelligent service degradation manager.
    
    Features:
    - Automatic performance monitoring
    - Multi-level degradation strategies
    - Service-specific adaptations
    - Fallback coordination
    - Recovery planning
    """
    
    def __init__(self,
                 default_level: ServiceLevel = ServiceLevel.FULL,
                 auto_recovery: bool = True,
                 monitoring_interval: int = 30):
        """
        Initialize graceful degradation service.
        
        Args:
            default_level: Default service level
            auto_recovery: Enable automatic recovery
            monitoring_interval: Health check interval in seconds
        """
        self.current_level = default_level
        self.auto_recovery = auto_recovery
        self.monitoring_interval = monitoring_interval
        
        # Service registry
        self.services: Dict[str, ServiceAdapter] = {}
        self.service_levels: Dict[str, ServiceLevel] = {}
        self.service_metrics: Dict[str, ServiceMetrics] = defaultdict(ServiceMetrics)
        
        # Degradation strategies
        self.strategies: List[FallbackStrategy] = self._initialize_strategies()
        self.active_degradations: Dict[str, datetime] = {}
        
        # Feature flags
        self.feature_flags: Dict[str, bool] = {
            'ai_generation': True,
            'video_processing': True,
            'high_quality_export': True,
            'real_time_preview': True,
            'batch_operations': True,
            'advanced_effects': True,
            'cloud_sync': True,
            'analytics': True
        }
        
        # Quality settings
        self.quality_settings: Dict[str, Any] = {
            'video_resolution': '1920x1080',
            'video_bitrate': '8M',
            'audio_bitrate': '192k',
            'image_quality': 95,
            'preview_fps': 30,
            'concurrent_operations': 5
        }
        
        # Monitoring task
        self._monitoring_task = None
        
        logger.info(
            "Graceful degradation service initialized",
            default_level=default_level.value,
            auto_recovery=auto_recovery
        )
    
    def _initialize_strategies(self) -> List[FallbackStrategy]:
        """Initialize default fallback strategies."""
        return [
            FallbackStrategy(
                name="high_cpu_degradation",
                target_level=ServiceLevel.REDUCED,
                conditions={'cpu_percent': 80, 'duration': 60},
                actions=['disable_real_time_preview', 'reduce_concurrent_operations'],
                priority=10
            ),
            FallbackStrategy(
                name="memory_pressure_degradation",
                target_level=ServiceLevel.MINIMAL,
                conditions={'memory_percent': 85, 'duration': 30},
                actions=['disable_advanced_effects', 'reduce_quality', 'limit_batch_size'],
                priority=20
            ),
            FallbackStrategy(
                name="api_rate_limit_degradation",
                target_level=ServiceLevel.REDUCED,
                conditions={'error_rate': 0.5, 'error_type': 'rate_limit'},
                actions=['enable_request_throttling', 'use_cached_results'],
                priority=15
            ),
            FallbackStrategy(
                name="critical_resource_degradation",
                target_level=ServiceLevel.EMERGENCY,
                conditions={'cpu_percent': 95, 'memory_percent': 95},
                actions=['disable_all_non_essential', 'emergency_mode'],
                priority=30
            )
        ]
    
    async def start_monitoring(self):
        """Start service health monitoring."""
        if self._monitoring_task:
            return
        
        self._monitoring_task = asyncio.create_task(self._monitor_health())
        logger.info("Health monitoring started")
    
    async def stop_monitoring(self):
        """Stop service health monitoring."""
        if self._monitoring_task:
            self._monitoring_task.cancel()
            self._monitoring_task = None
            logger.info("Health monitoring stopped")
    
    async def _monitor_health(self):
        """Monitor system and service health."""
        while True:
            try:
                # Update system metrics
                system_metrics = await self._collect_system_metrics()
                
                # Check each registered service
                for service_name in self.services:
                    await self._check_service_health(service_name)
                
                # Evaluate degradation strategies
                await self._evaluate_strategies(system_metrics)
                
                # Attempt recovery if enabled
                if self.auto_recovery:
                    await self._attempt_recovery()
                
                # Log current state
                logger.debug(
                    "Health check completed",
                    level=self.current_level.value,
                    active_degradations=list(self.active_degradations.keys())
                )
                
            except Exception as e:
                logger.error(
                    "Health monitoring error",
                    error=str(e)
                )
            
            await asyncio.sleep(self.monitoring_interval)
    
    async def _collect_system_metrics(self) -> Dict[str, float]:
        """Collect current system metrics."""
        return {
            'cpu_percent': psutil.cpu_percent(interval=1),
            'memory_percent': psutil.virtual_memory().percent,
            'disk_percent': psutil.disk_usage('/').percent,
            'network_connections': len(psutil.net_connections()),
            'timestamp': time.time()
        }
    
    async def _check_service_health(self, service_name: str):
        """Check health of specific service."""
        metrics = self.service_metrics[service_name]
        
        # Calculate error rate
        total_requests = metrics.success_count + metrics.error_count
        if total_requests > 0:
            metrics.error_rate = metrics.error_count / total_requests
        
        # Update timestamp
        metrics.last_updated = datetime.now()
    
    async def _evaluate_strategies(self, system_metrics: Dict[str, float]):
        """Evaluate and apply degradation strategies."""
        current_time = datetime.now()
        
        for strategy in sorted(self.strategies, key=lambda s: s.priority, reverse=True):
            # Check if strategy is already active
            if strategy.name in self.active_degradations:
                # Check cooldown
                activation_time = self.active_degradations[strategy.name]
                if (current_time - activation_time).seconds < strategy.cooldown_seconds:
                    continue
            
            # Evaluate conditions
            if self._check_conditions(strategy.conditions, system_metrics):
                await self._apply_degradation(strategy)
    
    def _check_conditions(self, conditions: Dict[str, Any], metrics: Dict[str, float]) -> bool:
        """Check if degradation conditions are met."""
        for metric, threshold in conditions.items():
            if metric == 'duration':
                continue  # Duration is handled separately
            
            if metric in metrics:
                if isinstance(threshold, (int, float)):
                    if metrics[metric] < threshold:
                        return False
                elif isinstance(threshold, str):
                    if metrics.get(metric) != threshold:
                        return False
        
        return True
    
    async def _apply_degradation(self, strategy: FallbackStrategy):
        """Apply degradation strategy."""
        logger.warning(
            "Applying degradation strategy",
            strategy=strategy.name,
            target_level=strategy.target_level.value
        )
        
        # Record activation
        self.active_degradations[strategy.name] = datetime.now()
        
        # Apply actions
        for action in strategy.actions:
            await self._execute_action(action)
        
        # Update service level
        await self.set_service_level(strategy.target_level)
    
    async def _execute_action(self, action: str):
        """Execute degradation action."""
        try:
            if action == 'disable_real_time_preview':
                self.feature_flags['real_time_preview'] = False
                
            elif action == 'reduce_concurrent_operations':
                self.quality_settings['concurrent_operations'] = max(1, 
                    self.quality_settings['concurrent_operations'] // 2)
                
            elif action == 'disable_advanced_effects':
                self.feature_flags['advanced_effects'] = False
                
            elif action == 'reduce_quality':
                await self._reduce_quality_settings()
                
            elif action == 'limit_batch_size':
                self.feature_flags['batch_operations'] = False
                
            elif action == 'enable_request_throttling':
                # Implement request throttling
                pass
                
            elif action == 'use_cached_results':
                # Enable aggressive caching
                pass
                
            elif action == 'disable_all_non_essential':
                await self._emergency_mode()
                
            elif action == 'emergency_mode':
                await self._emergency_mode()
            
            logger.info(f"Executed degradation action: {action}")
            
        except Exception as e:
            logger.error(
                "Failed to execute action",
                action=action,
                error=str(e)
            )
    
    async def _reduce_quality_settings(self):
        """Reduce quality settings for resource conservation."""
        # Reduce video quality
        if self.quality_settings['video_resolution'] == '1920x1080':
            self.quality_settings['video_resolution'] = '1280x720'
        elif self.quality_settings['video_resolution'] == '1280x720':
            self.quality_settings['video_resolution'] = '854x480'
        
        # Reduce bitrates
        self.quality_settings['video_bitrate'] = '4M'
        self.quality_settings['audio_bitrate'] = '128k'
        
        # Reduce image quality
        self.quality_settings['image_quality'] = max(70, 
            self.quality_settings['image_quality'] - 10)
        
        # Reduce preview FPS
        self.quality_settings['preview_fps'] = max(15, 
            self.quality_settings['preview_fps'] // 2)
        
        logger.info("Quality settings reduced", settings=self.quality_settings)
    
    async def _emergency_mode(self):
        """Enable emergency mode - minimal functionality only."""
        # Disable all non-essential features
        self.feature_flags = {
            'ai_generation': True,      # Keep core functionality
            'video_processing': True,    # Keep core functionality
            'high_quality_export': False,
            'real_time_preview': False,
            'batch_operations': False,
            'advanced_effects': False,
            'cloud_sync': False,
            'analytics': False
        }
        
        # Minimum quality settings
        self.quality_settings = {
            'video_resolution': '854x480',
            'video_bitrate': '2M',
            'audio_bitrate': '96k',
            'image_quality': 70,
            'preview_fps': 15,
            'concurrent_operations': 1
        }
        
        logger.warning("Emergency mode activated")
    
    async def _attempt_recovery(self):
        """Attempt to recover to higher service levels."""
        if self.current_level == ServiceLevel.FULL:
            return
        
        # Check if conditions have improved
        system_metrics = await self._collect_system_metrics()
        
        # Define recovery thresholds (lower than degradation thresholds)
        recovery_conditions = {
            ServiceLevel.EMERGENCY: {
                'cpu_percent': 70,
                'memory_percent': 70
            },
            ServiceLevel.MINIMAL: {
                'cpu_percent': 60,
                'memory_percent': 60
            },
            ServiceLevel.REDUCED: {
                'cpu_percent': 50,
                'memory_percent': 50
            }
        }
        
        # Check if we can recover
        current_conditions = recovery_conditions.get(self.current_level, {})
        can_recover = all(
            system_metrics.get(metric, 100) < threshold
            for metric, threshold in current_conditions.items()
        )
        
        if can_recover:
            # Recover to next level
            next_level = self._get_next_recovery_level()
            if next_level:
                logger.info(
                    "Attempting recovery",
                    from_level=self.current_level.value,
                    to_level=next_level.value
                )
                await self.set_service_level(next_level)
                
                # Clear some degradations
                self.active_degradations.clear()
    
    def _get_next_recovery_level(self) -> Optional[ServiceLevel]:
        """Get next recovery level."""
        level_order = [
            ServiceLevel.OFFLINE,
            ServiceLevel.EMERGENCY,
            ServiceLevel.MINIMAL,
            ServiceLevel.REDUCED,
            ServiceLevel.FULL
        ]
        
        current_index = level_order.index(self.current_level)
        if current_index < len(level_order) - 1:
            return level_order[current_index + 1]
        return None
    
    async def set_service_level(self, level: ServiceLevel, reason: Optional[DegradationReason] = None):
        """Set service level with optional reason."""
        if level == self.current_level:
            return
        
        old_level = self.current_level
        self.current_level = level
        
        logger.info(
            "Service level changed",
            from_level=old_level.value,
            to_level=level.value,
            reason=reason.value if reason else None
        )
        
        # Notify all registered services
        for service_name, adapter in self.services.items():
            try:
                success = await adapter.adapt_to_level(level)
                self.service_levels[service_name] = level if success else old_level
            except Exception as e:
                logger.error(
                    "Service adaptation failed",
                    service=service_name,
                    error=str(e)
                )
        
        # Adjust feature flags based on level
        await self._adjust_features_for_level(level)
    
    async def _adjust_features_for_level(self, level: ServiceLevel):
        """Adjust feature flags based on service level."""
        if level == ServiceLevel.FULL:
            # Enable all features
            self.feature_flags = {k: True for k in self.feature_flags}
            
        elif level == ServiceLevel.REDUCED:
            # Disable some features
            self.feature_flags['real_time_preview'] = False
            self.feature_flags['advanced_effects'] = False
            self.feature_flags['cloud_sync'] = False
            
        elif level == ServiceLevel.MINIMAL:
            # Keep only essential features
            self.feature_flags = {
                'ai_generation': True,
                'video_processing': True,
                'high_quality_export': False,
                'real_time_preview': False,
                'batch_operations': False,
                'advanced_effects': False,
                'cloud_sync': False,
                'analytics': False
            }
            
        elif level == ServiceLevel.EMERGENCY:
            await self._emergency_mode()
    
    def register_service(self, name: str, adapter: ServiceAdapter):
        """Register a service with its adapter."""
        self.services[name] = adapter
        self.service_levels[name] = self.current_level
        logger.info(f"Service registered: {name}")
    
    def update_service_metrics(self, 
                             service_name: str,
                             success: bool = True,
                             response_time_ms: float = 0.0):
        """Update metrics for a service."""
        metrics = self.service_metrics[service_name]
        
        if success:
            metrics.success_count += 1
        else:
            metrics.error_count += 1
        
        # Update response time (exponential moving average)
        alpha = 0.1  # Smoothing factor
        metrics.response_time_ms = (alpha * response_time_ms + 
                                   (1 - alpha) * metrics.response_time_ms)
        
        metrics.last_updated = datetime.now()
    
    def is_feature_enabled(self, feature: str) -> bool:
        """Check if a feature is currently enabled."""
        return self.feature_flags.get(feature, False)
    
    def get_quality_setting(self, setting: str) -> Any:
        """Get current quality setting."""
        return self.quality_settings.get(setting)
    
    def get_status(self) -> Dict[str, Any]:
        """Get current degradation status."""
        return {
            'current_level': self.current_level.value,
            'service_levels': {name: level.value for name, level in self.service_levels.items()},
            'active_degradations': list(self.active_degradations.keys()),
            'feature_flags': self.feature_flags,
            'quality_settings': self.quality_settings,
            'metrics': {
                name: {
                    'response_time_ms': metrics.response_time_ms,
                    'error_rate': metrics.error_rate,
                    'last_updated': metrics.last_updated.isoformat()
                }
                for name, metrics in self.service_metrics.items()
            }
        }
    
    async def force_degradation(self, level: ServiceLevel, duration_minutes: int = 60):
        """Force degradation for testing or manual intervention."""
        await self.set_service_level(level, DegradationReason.MANUAL_OVERRIDE)
        
        # Schedule recovery
        if duration_minutes > 0:
            asyncio.create_task(self._scheduled_recovery(duration_minutes))
    
    async def _scheduled_recovery(self, duration_minutes: int):
        """Schedule automatic recovery after forced degradation."""
        await asyncio.sleep(duration_minutes * 60)
        
        logger.info("Scheduled recovery initiated")
        await self.set_service_level(ServiceLevel.FULL)


# Example service adapters
class OpenAIServiceAdapter(ServiceAdapter):
    """Adapter for OpenAI service degradation."""
    
    async def adapt_to_level(self, level: ServiceLevel) -> bool:
        """Adapt OpenAI service to level."""
        try:
            if level == ServiceLevel.FULL:
                # Use best models
                self.model = "gpt-4"
                self.max_tokens = 4000
                
            elif level == ServiceLevel.REDUCED:
                # Use cheaper models
                self.model = "gpt-3.5-turbo"
                self.max_tokens = 2000
                
            elif level == ServiceLevel.MINIMAL:
                # Minimal usage
                self.model = "gpt-3.5-turbo"
                self.max_tokens = 1000
                
            elif level == ServiceLevel.EMERGENCY:
                # Cache only, no new requests
                self.model = None
                self.max_tokens = 0
            
            return True
            
        except Exception:
            return False
    
    def get_current_capabilities(self) -> Dict[str, Any]:
        """Get current OpenAI capabilities."""
        return {
            'model': getattr(self, 'model', 'gpt-4'),
            'max_tokens': getattr(self, 'max_tokens', 4000),
            'available': self.model is not None
        }


class VideoProcessingAdapter(ServiceAdapter):
    """Adapter for video processing degradation."""
    
    async def adapt_to_level(self, level: ServiceLevel) -> bool:
        """Adapt video processing to level."""
        try:
            if level == ServiceLevel.FULL:
                self.max_resolution = "1920x1080"
                self.max_bitrate = "10M"
                self.concurrent_jobs = 5
                
            elif level == ServiceLevel.REDUCED:
                self.max_resolution = "1280x720"
                self.max_bitrate = "5M"
                self.concurrent_jobs = 3
                
            elif level == ServiceLevel.MINIMAL:
                self.max_resolution = "854x480"
                self.max_bitrate = "2M"
                self.concurrent_jobs = 1
                
            elif level == ServiceLevel.EMERGENCY:
                self.max_resolution = "640x360"
                self.max_bitrate = "1M"
                self.concurrent_jobs = 1
            
            return True
            
        except Exception:
            return False
    
    def get_current_capabilities(self) -> Dict[str, Any]:
        """Get current video processing capabilities."""
        return {
            'max_resolution': getattr(self, 'max_resolution', '1920x1080'),
            'max_bitrate': getattr(self, 'max_bitrate', '10M'),
            'concurrent_jobs': getattr(self, 'concurrent_jobs', 5)
        }


# Global instance
degradation_service = GracefulDegradationService()

# Register default adapters
degradation_service.register_service('openai', OpenAIServiceAdapter())
degradation_service.register_service('video_processing', VideoProcessingAdapter())