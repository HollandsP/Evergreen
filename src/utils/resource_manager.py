"""
Resource Manager

Manages system resources like memory and CPU usage to prevent
resource exhaustion during video generation operations.
"""

import asyncio
import psutil
import time
from contextlib import asynccontextmanager
from typing import Dict, Any, Optional
from dataclasses import dataclass

import structlog

logger = structlog.get_logger()


@dataclass
class ResourceLimits:
    """Resource limit configuration."""
    memory_mb: int = 4096
    cpu_cores: int = 4
    disk_space_mb: int = 10240
    max_concurrent_operations: int = 3


@dataclass 
class ResourceUsage:
    """Current resource usage."""
    memory_used_mb: float
    memory_available_mb: float
    cpu_percent: float
    disk_used_mb: float
    disk_available_mb: float
    active_operations: int


class ResourceManager:
    """
    Manages system resources to prevent overload during video generation.
    
    Tracks memory, CPU, and disk usage and provides resource allocation
    with proper cleanup guarantees.
    """
    
    def __init__(self, limits: Optional[ResourceLimits] = None):
        """
        Initialize resource manager.
        
        Args:
            limits: Resource limit configuration
        """
        self.limits = limits or ResourceLimits()
        self.active_operations = 0
        self.operation_semaphore = asyncio.Semaphore(self.limits.max_concurrent_operations)
        
        # Track allocated resources
        self.allocated_memory = 0
        self.allocated_cpu = 0
        
        logger.info(
            "Resource manager initialized",
            memory_limit_mb=self.limits.memory_mb,
            cpu_limit=self.limits.cpu_cores,
            max_concurrent=self.limits.max_concurrent_operations
        )
    
    async def check_available_resources(self) -> ResourceUsage:
        """
        Check current system resource usage.
        
        Returns:
            Current resource usage information
        """
        # Get memory info
        memory = psutil.virtual_memory()
        memory_used_mb = memory.used / 1024 / 1024
        memory_available_mb = memory.available / 1024 / 1024
        
        # Get CPU usage
        cpu_percent = psutil.cpu_percent(interval=0.1)
        
        # Get disk usage for temp directory
        disk = psutil.disk_usage('/tmp' if hasattr(psutil, 'disk_usage') else '.')
        disk_used_mb = disk.used / 1024 / 1024
        disk_available_mb = disk.free / 1024 / 1024
        
        usage = ResourceUsage(
            memory_used_mb=memory_used_mb,
            memory_available_mb=memory_available_mb,
            cpu_percent=cpu_percent,
            disk_used_mb=disk_used_mb,
            disk_available_mb=disk_available_mb,
            active_operations=self.active_operations
        )
        
        logger.debug(
            "Resource usage check",
            memory_used_mb=round(memory_used_mb, 1),
            memory_available_mb=round(memory_available_mb, 1),
            cpu_percent=round(cpu_percent, 1),
            disk_available_mb=round(disk_available_mb, 1),
            active_operations=self.active_operations
        )
        
        return usage
    
    async def can_allocate_resources(self, memory_mb: int, cpu_cores: int) -> bool:
        """
        Check if requested resources can be allocated.
        
        Args:
            memory_mb: Required memory in MB
            cpu_cores: Required CPU cores
            
        Returns:
            True if resources can be allocated
        """
        usage = await self.check_available_resources()
        
        # Check if we have enough available resources
        memory_ok = usage.memory_available_mb >= memory_mb
        cpu_ok = usage.cpu_percent < 80.0  # Don't allocate if CPU usage too high
        disk_ok = usage.disk_available_mb >= self.limits.disk_space_mb
        operations_ok = self.active_operations < self.limits.max_concurrent_operations
        
        can_allocate = memory_ok and cpu_ok and disk_ok and operations_ok
        
        if not can_allocate:
            logger.warning(
                "Cannot allocate requested resources",
                requested_memory_mb=memory_mb,
                requested_cpu_cores=cpu_cores,
                memory_available=usage.memory_available_mb,
                cpu_percent=usage.cpu_percent,
                disk_available=usage.disk_available_mb,
                active_operations=self.active_operations,
                memory_ok=memory_ok,
                cpu_ok=cpu_ok,
                disk_ok=disk_ok,
                operations_ok=operations_ok
            )
        
        return can_allocate
    
    @asynccontextmanager
    async def acquire_resources(self, memory_mb: int = 512, cpu_cores: int = 1):
        """
        Context manager for resource allocation with automatic cleanup.
        
        Args:
            memory_mb: Required memory in MB
            cpu_cores: Required CPU cores
            
        Yields:
            Resource allocation context
            
        Raises:
            ResourceError: If resources cannot be allocated
        """
        # Wait for operation slot
        await self.operation_semaphore.acquire()
        
        try:
            # Check if resources are available
            if not await self.can_allocate_resources(memory_mb, cpu_cores):
                # Wait a bit and try again
                await asyncio.sleep(1.0)
                if not await self.can_allocate_resources(memory_mb, cpu_cores):
                    raise ResourceError(
                        f"Cannot allocate resources: {memory_mb}MB memory, {cpu_cores} CPU cores"
                    )
            
            # Allocate resources
            self.allocated_memory += memory_mb
            self.allocated_cpu += cpu_cores
            self.active_operations += 1
            
            logger.info(
                "Resources allocated",
                memory_mb=memory_mb,
                cpu_cores=cpu_cores,
                total_allocated_memory=self.allocated_memory,
                total_allocated_cpu=self.allocated_cpu,
                active_operations=self.active_operations
            )
            
            start_time = time.time()
            
            try:
                yield {
                    'memory_mb': memory_mb,
                    'cpu_cores': cpu_cores,
                    'start_time': start_time
                }
            finally:
                # Always clean up resources
                self.allocated_memory -= memory_mb
                self.allocated_cpu -= cpu_cores  
                self.active_operations -= 1
                
                duration = time.time() - start_time
                
                logger.info(
                    "Resources released",
                    memory_mb=memory_mb,
                    cpu_cores=cpu_cores,
                    duration_seconds=round(duration, 2),
                    remaining_allocated_memory=self.allocated_memory,
                    remaining_allocated_cpu=self.allocated_cpu,
                    active_operations=self.active_operations
                )
                
        finally:
            # Release semaphore
            self.operation_semaphore.release()
    
    def get_usage_stats(self) -> Dict[str, Any]:
        """Get current resource usage statistics."""
        try:
            memory = psutil.virtual_memory()
            cpu_count = psutil.cpu_count()
            cpu_percent = psutil.cpu_percent()
            
            return {
                'memory': {
                    'total_mb': round(memory.total / 1024 / 1024, 1),
                    'used_mb': round(memory.used / 1024 / 1024, 1),
                    'available_mb': round(memory.available / 1024 / 1024, 1),
                    'allocated_mb': self.allocated_memory,
                    'percent_used': round(memory.percent, 1)
                },
                'cpu': {
                    'total_cores': cpu_count,
                    'allocated_cores': self.allocated_cpu,
                    'percent_used': round(cpu_percent, 1)
                },
                'operations': {
                    'active': self.active_operations,
                    'max_concurrent': self.limits.max_concurrent_operations,
                    'available_slots': self.limits.max_concurrent_operations - self.active_operations
                }
            }
        except Exception as e:
            logger.warning("Failed to get usage stats", error=str(e))
            return {
                'error': str(e),
                'active_operations': self.active_operations,
                'allocated_memory_mb': self.allocated_memory,
                'allocated_cpu': self.allocated_cpu
            }
    
    async def wait_for_resources(self, memory_mb: int, cpu_cores: int, 
                               timeout: float = 300.0) -> bool:
        """
        Wait for resources to become available.
        
        Args:
            memory_mb: Required memory in MB
            cpu_cores: Required CPU cores
            timeout: Maximum time to wait in seconds
            
        Returns:
            True if resources became available, False if timeout
        """
        start_time = time.time()
        check_interval = 5.0  # Check every 5 seconds
        
        while time.time() - start_time < timeout:
            if await self.can_allocate_resources(memory_mb, cpu_cores):
                return True
            
            logger.info(
                "Waiting for resources to become available",
                required_memory_mb=memory_mb,
                required_cpu_cores=cpu_cores,
                elapsed_seconds=round(time.time() - start_time, 1),
                timeout_seconds=timeout
            )
            
            await asyncio.sleep(check_interval)
        
        logger.warning(
            "Timeout waiting for resources",
            required_memory_mb=memory_mb,
            required_cpu_cores=cpu_cores,
            timeout_seconds=timeout
        )
        return False
    
    def get_resource_recommendations(self) -> Dict[str, Any]:
        """Get recommendations for resource optimization."""
        try:
            usage = asyncio.get_event_loop().run_until_complete(
                self.check_available_resources()
            )
            
            recommendations = []
            
            if usage.memory_available_mb < 1024:
                recommendations.append("Consider increasing available memory (< 1GB free)")
            
            if usage.cpu_percent > 90:
                recommendations.append("CPU usage very high (> 90%)")
            
            if usage.disk_available_mb < 5120:
                recommendations.append("Low disk space (< 5GB free)")
            
            if self.active_operations >= self.limits.max_concurrent_operations:
                recommendations.append("All operation slots in use")
            
            return {
                'current_usage': usage.__dict__,
                'recommendations': recommendations,
                'status': 'good' if not recommendations else 'warning'
            }
            
        except Exception as e:
            logger.warning("Failed to get recommendations", error=str(e))
            return {
                'error': str(e),
                'status': 'unknown'
            }


class ResourceError(Exception):
    """Raised when resources cannot be allocated."""
    pass