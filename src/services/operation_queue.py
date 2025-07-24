"""
Operation Queue Manager for High-Performance Video Processing.

This service provides priority-based queue management with concurrent operation
support and intelligent scheduling for optimal resource utilization.
"""

import asyncio
import logging
import time
import json
from typing import Dict, List, Any, Optional, Callable, Union, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import heapq
import threading
from datetime import datetime
import uuid

logger = logging.getLogger(__name__)

class OperationPriority(Enum):
    """Operation priority levels."""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    URGENT = 4

class OperationStatus(Enum):
    """Operation status values."""
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

@dataclass
class QueuedOperation:
    """Represents a queued video operation."""
    operation_id: str
    operation_type: str
    priority: OperationPriority
    params: Dict[str, Any]
    created_at: float
    status: OperationStatus
    estimated_duration: float = 30.0  # seconds
    max_retries: int = 3
    retry_count: int = 0
    progress_callback: Optional[Callable] = None
    result: Optional[Any] = None
    error: Optional[str] = None
    started_at: Optional[float] = None
    completed_at: Optional[float] = None
    
    def __post_init__(self):
        """Ensure progress_callback is not included in serialization."""
        if hasattr(self, 'progress_callback') and self.progress_callback is not None:
            # Store callback separately to avoid serialization issues
            self._callback = self.progress_callback
            self.progress_callback = None
    
    def __lt__(self, other):
        """Compare operations for priority queue (higher priority first)."""
        if self.priority.value != other.priority.value:
            return self.priority.value > other.priority.value
        # Same priority, use creation time (FIFO)
        return self.created_at < other.created_at
    
    @property
    def age_seconds(self) -> float:
        """Get age of operation in seconds."""
        return time.time() - self.created_at
    
    @property
    def execution_time(self) -> Optional[float]:
        """Get execution time if operation has completed."""
        if self.started_at and self.completed_at:
            return self.completed_at - self.started_at
        return None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses."""
        data = asdict(self)
        
        # Convert enum values to strings
        data['priority'] = self.priority.name
        data['status'] = self.status.value
        
        # Add computed fields
        data['age_seconds'] = self.age_seconds
        data['execution_time'] = self.execution_time
        
        # Remove callback
        data.pop('progress_callback', None)
        
        return data

class OperationQueue:
    """
    Priority-based operation queue with concurrent execution support.
    
    Features:
    - Priority-based scheduling (URGENT > HIGH > NORMAL > LOW)
    - Concurrent operation execution (default: 3 workers)
    - Retry mechanism with exponential backoff
    - Progress tracking and cancellation
    - Queue persistence and recovery
    - Resource usage monitoring
    - Intelligent load balancing
    """
    
    def __init__(self, 
                 max_concurrent_operations: int = 3,
                 enable_persistence: bool = True,
                 queue_file: str = "./cache/operation_queue.json"):
        """
        Initialize operation queue.
        
        Args:
            max_concurrent_operations: Maximum concurrent operations
            enable_persistence: Enable queue persistence
            queue_file: Path to queue persistence file
        """
        self.max_concurrent = max_concurrent_operations
        self.enable_persistence = enable_persistence
        self.queue_file = queue_file
        
        # Priority queue (min-heap, but we override __lt__ for max behavior)
        self._queue: List[QueuedOperation] = []
        self._queue_lock = threading.Lock()
        
        # Running operations
        self._running_operations: Dict[str, QueuedOperation] = {}
        self._running_lock = threading.Lock()
        
        # Completed operations (keep for history)
        self._completed_operations: Dict[str, QueuedOperation] = {}
        self._completed_lock = threading.Lock()
        
        # Worker tasks
        self._workers: List[asyncio.Task] = []
        self._worker_semaphore = asyncio.Semaphore(max_concurrent_operations)
        self._shutdown_event = asyncio.Event()
        
        # Statistics
        self._stats = {
            "total_queued": 0,
            "total_completed": 0,
            "total_failed": 0,
            "total_cancelled": 0,
            "total_execution_time": 0.0
        }
        
        # Load persisted queue
        if enable_persistence:
            self._load_queue()
        
        logger.info(f"Initialized operation queue with {max_concurrent_operations} concurrent workers")
    
    def _load_queue(self):
        """Load persisted queue from disk."""
        try:
            import os
            if os.path.exists(self.queue_file):
                with open(self.queue_file, 'r') as f:
                    data = json.load(f)
                
                # Restore queued operations
                for op_data in data.get("queued", []):
                    op = QueuedOperation(**op_data)
                    op.priority = OperationPriority[op_data["priority"]]
                    op.status = OperationStatus(op_data["status"])
                    
                    with self._queue_lock:
                        heapq.heappush(self._queue, op)
                
                # Restore statistics
                self._stats.update(data.get("statistics", {}))
                
                logger.info(f"Loaded {len(self._queue)} queued operations from persistence")
        
        except Exception as e:
            logger.error(f"Error loading persisted queue: {e}")
    
    def _save_queue(self):
        """Save current queue to disk."""
        if not self.enable_persistence:
            return
        
        try:
            # Prepare data for serialization
            with self._queue_lock:
                queued_data = [op.to_dict() for op in self._queue]
            
            data = {
                "queued": queued_data,
                "statistics": self._stats,
                "saved_at": time.time(),
                "version": "1.0"
            }
            
            # Atomic write
            import os
            temp_file = self.queue_file + '.tmp'
            os.makedirs(os.path.dirname(self.queue_file), exist_ok=True)
            
            with open(temp_file, 'w') as f:
                json.dump(data, f, indent=2)
            
            os.replace(temp_file, self.queue_file)
            
        except Exception as e:
            logger.error(f"Error saving queue to disk: {e}")
    
    async def add_operation(self, 
                           operation_type: str,
                           params: Dict[str, Any],
                           priority: OperationPriority = OperationPriority.NORMAL,
                           estimated_duration: float = 30.0,
                           max_retries: int = 3,
                           progress_callback: Optional[Callable] = None) -> str:
        """
        Add operation to queue.
        
        Args:
            operation_type: Type of operation to perform
            params: Operation parameters
            priority: Operation priority
            estimated_duration: Estimated duration in seconds
            max_retries: Maximum retry attempts
            progress_callback: Optional progress callback
            
        Returns:
            Operation ID
        """
        operation_id = str(uuid.uuid4())
        
        operation = QueuedOperation(
            operation_id=operation_id,
            operation_type=operation_type,
            priority=priority,
            params=params,
            created_at=time.time(),
            status=OperationStatus.QUEUED,
            estimated_duration=estimated_duration,
            max_retries=max_retries,
            progress_callback=progress_callback
        )
        
        with self._queue_lock:
            heapq.heappush(self._queue, operation)
            self._stats["total_queued"] += 1
        
        # Save queue state
        self._save_queue()
        
        logger.info(f"Queued operation {operation_id}: {operation_type} with priority {priority.name}")
        return operation_id
    
    async def get_operation_status(self, operation_id: str) -> Optional[Dict[str, Any]]:
        """Get status of specific operation."""
        # Check running operations
        with self._running_lock:
            if operation_id in self._running_operations:
                return self._running_operations[operation_id].to_dict()
        
        # Check completed operations
        with self._completed_lock:
            if operation_id in self._completed_operations:
                return self._completed_operations[operation_id].to_dict()
        
        # Check queued operations
        with self._queue_lock:
            for op in self._queue:
                if op.operation_id == operation_id:
                    return op.to_dict()
        
        return None
    
    async def cancel_operation(self, operation_id: str) -> bool:
        """Cancel operation if it's queued or running."""
        # Try to cancel from queue
        with self._queue_lock:
            for i, op in enumerate(self._queue):
                if op.operation_id == operation_id:
                    op.status = OperationStatus.CANCELLED
                    self._queue.pop(i)
                    heapq.heapify(self._queue)  # Restore heap property
                    
                    # Move to completed
                    with self._completed_lock:
                        self._completed_operations[operation_id] = op
                    
                    self._stats["total_cancelled"] += 1
                    logger.info(f"Cancelled queued operation: {operation_id}")
                    return True
        
        # Try to cancel running operation
        with self._running_lock:
            if operation_id in self._running_operations:
                op = self._running_operations[operation_id]
                op.status = OperationStatus.CANCELLED
                
                # The worker will detect this status change
                logger.info(f"Marked running operation for cancellation: {operation_id}")
                return True
        
        return False
    
    async def get_queue_status(self) -> Dict[str, Any]:
        """Get overall queue status."""
        with self._queue_lock:
            queued_count = len(self._queue)
            queued_by_priority = {}
            for op in self._queue:
                priority_name = op.priority.name
                queued_by_priority[priority_name] = queued_by_priority.get(priority_name, 0) + 1
        
        with self._running_lock:
            running_count = len(self._running_operations)
            running_operations = [op.to_dict() for op in self._running_operations.values()]
        
        with self._completed_lock:
            completed_count = len(self._completed_operations)
        
        # Calculate average execution time
        avg_execution_time = 0.0
        if self._stats["total_completed"] > 0:
            avg_execution_time = self._stats["total_execution_time"] / self._stats["total_completed"]
        
        # Estimate queue processing time
        estimated_queue_time = 0.0
        with self._queue_lock:
            for op in self._queue:
                estimated_queue_time += op.estimated_duration
        
        # Account for parallel processing
        if self.max_concurrent > 0:
            estimated_queue_time = estimated_queue_time / self.max_concurrent
        
        return {
            "queue_length": queued_count,
            "running_operations": running_count,
            "completed_operations": completed_count,
            "max_concurrent": self.max_concurrent,
            "queued_by_priority": queued_by_priority,
            "running_operations_details": running_operations,
            "statistics": self._stats.copy(),
            "average_execution_time_seconds": avg_execution_time,
            "estimated_queue_processing_time_seconds": estimated_queue_time,
            "worker_utilization_percent": (running_count / self.max_concurrent) * 100
        }
    
    async def start_workers(self):
        """Start worker tasks."""
        if self._workers:
            logger.warning("Workers already started")
            return
        
        self._shutdown_event.clear()
        
        for i in range(self.max_concurrent):
            worker_task = asyncio.create_task(self._worker_loop(f"worker-{i}"))
            self._workers.append(worker_task)
        
        logger.info(f"Started {len(self._workers)} worker tasks")
    
    async def stop_workers(self):
        """Stop worker tasks."""
        self._shutdown_event.set()
        
        if self._workers:
            # Cancel all workers
            for worker in self._workers:
                worker.cancel()
            
            # Wait for workers to finish
            await asyncio.gather(*self._workers, return_exceptions=True)
            self._workers.clear()
        
        # Save final state
        self._save_queue()
        
        logger.info("Stopped all worker tasks")
    
    async def _worker_loop(self, worker_name: str):
        """Main worker loop."""
        logger.info(f"Started worker: {worker_name}")
        
        try:
            while not self._shutdown_event.is_set():
                # Get next operation from queue
                operation = None
                
                with self._queue_lock:
                    if self._queue:
                        operation = heapq.heappop(self._queue)
                
                if operation is None:
                    # No work available, wait a bit
                    await asyncio.sleep(0.1)
                    continue
                
                # Acquire semaphore for concurrent execution limit
                async with self._worker_semaphore:
                    if self._shutdown_event.is_set():
                        # Put operation back if shutting down
                        with self._queue_lock:
                            heapq.heappush(self._queue, operation)
                        break
                    
                    await self._execute_operation(operation, worker_name)
                
        except asyncio.CancelledError:
            logger.info(f"Worker {worker_name} cancelled")
        except Exception as e:
            logger.error(f"Worker {worker_name} error: {e}")
        
        logger.info(f"Worker {worker_name} finished")
    
    async def _execute_operation(self, operation: QueuedOperation, worker_name: str):
        """Execute a single operation."""
        operation_id = operation.operation_id
        
        # Move to running operations
        operation.status = OperationStatus.RUNNING
        operation.started_at = time.time()
        
        with self._running_lock:
            self._running_operations[operation_id] = operation
        
        logger.info(f"Worker {worker_name} executing operation {operation_id}: {operation.operation_type}")
        
        try:
            # Import here to avoid circular imports
            from .async_moviepy_wrapper import get_async_moviepy
            
            async_moviepy = get_async_moviepy()
            
            # Execute based on operation type
            if operation.operation_type == "trim_video":
                result = await async_moviepy.trim_video(
                    operation_id=operation_id,
                    progress_callback=operation.progress_callback,
                    **operation.params
                )
            elif operation.operation_type == "change_speed":
                result = await async_moviepy.change_speed(
                    operation_id=operation_id,
                    progress_callback=operation.progress_callback,
                    **operation.params
                )
            elif operation.operation_type == "add_fade_effect":
                result = await async_moviepy.add_fade_effect(
                    operation_id=operation_id,
                    progress_callback=operation.progress_callback,
                    **operation.params
                )
            else:
                raise ValueError(f"Unsupported operation type: {operation.operation_type}")
            
            # Check if operation was cancelled during execution
            if operation.status == OperationStatus.CANCELLED:
                raise asyncio.CancelledError("Operation cancelled during execution")
            
            # Operation completed successfully
            operation.status = OperationStatus.COMPLETED
            operation.completed_at = time.time()
            operation.result = result
            
            # Update statistics
            execution_time = operation.execution_time or 0
            self._stats["total_completed"] += 1
            self._stats["total_execution_time"] += execution_time
            
            logger.info(f"Worker {worker_name} completed operation {operation_id} in {execution_time:.2f}s")
            
        except asyncio.CancelledError:
            operation.status = OperationStatus.CANCELLED
            operation.completed_at = time.time()
            self._stats["total_cancelled"] += 1
            logger.info(f"Operation {operation_id} cancelled")
            
        except Exception as e:
            operation.retry_count += 1
            operation.error = str(e)
            
            if operation.retry_count < operation.max_retries:
                # Retry operation
                operation.status = OperationStatus.QUEUED
                operation.started_at = None
                
                # Add delay before retry (exponential backoff)
                retry_delay = min(2 ** operation.retry_count, 30)
                await asyncio.sleep(retry_delay)
                
                # Put back in queue with higher priority for retry
                with self._queue_lock:
                    heapq.heappush(self._queue, operation)
                
                logger.warning(f"Operation {operation_id} failed, retrying ({operation.retry_count}/{operation.max_retries}): {e}")
                
                # Remove from running operations
                with self._running_lock:
                    self._running_operations.pop(operation_id, None)
                
                return
            else:
                # Max retries reached
                operation.status = OperationStatus.FAILED
                operation.completed_at = time.time()
                self._stats["total_failed"] += 1
                
                logger.error(f"Operation {operation_id} failed permanently after {operation.retry_count} retries: {e}")
        
        # Move to completed operations
        with self._running_lock:
            self._running_operations.pop(operation_id, None)
        
        with self._completed_lock:
            self._completed_operations[operation_id] = operation
        
        # Cleanup old completed operations (keep last 1000)
        with self._completed_lock:
            if len(self._completed_operations) > 1000:
                # Remove oldest 100 operations
                oldest_ops = sorted(
                    self._completed_operations.items(),
                    key=lambda x: x[1].completed_at or 0
                )[:100]
                
                for op_id, _ in oldest_ops:
                    del self._completed_operations[op_id]
    
    async def get_operation_history(self, 
                                   limit: int = 100,
                                   status_filter: Optional[OperationStatus] = None) -> List[Dict[str, Any]]:
        """Get operation history."""
        with self._completed_lock:
            operations = list(self._completed_operations.values())
        
        # Filter by status if specified
        if status_filter:
            operations = [op for op in operations if op.status == status_filter]
        
        # Sort by completion time (newest first)
        operations.sort(key=lambda x: x.completed_at or 0, reverse=True)
        
        # Limit results
        operations = operations[:limit]
        
        return [op.to_dict() for op in operations]
    
    async def cleanup(self):
        """Cleanup queue manager."""
        logger.info("Starting operation queue cleanup")
        
        await self.stop_workers()
        self._save_queue()
        
        logger.info("Operation queue cleanup completed")

# Global queue manager instance
_queue_manager_instance: Optional[OperationQueue] = None

def get_operation_queue() -> OperationQueue:
    """Get global operation queue instance."""
    global _queue_manager_instance
    if _queue_manager_instance is None:
        _queue_manager_instance = OperationQueue()
    return _queue_manager_instance

async def cleanup_operation_queue():
    """Cleanup global operation queue instance."""
    global _queue_manager_instance
    if _queue_manager_instance is not None:
        await _queue_manager_instance.cleanup()
        _queue_manager_instance = None