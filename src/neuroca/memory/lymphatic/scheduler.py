"""
Lymphatic Memory Scheduler Module

This module implements the scheduling system for the lymphatic memory tier in the
NeuroCognitive Architecture (NCA). The lymphatic memory system is responsible for
memory consolidation, cleanup, and maintenance tasks that occur during periods of
lower activity (similar to how the human lymphatic system operates during rest).

The scheduler manages:
1. Periodic memory consolidation from working memory to long-term storage
2. Cleanup of obsolete or low-relevance memories
3. Optimization and reorganization of memory structures
4. Priority-based scheduling of maintenance tasks
5. Adaptive scheduling based on system load and urgency

Usage:
    scheduler = LymphaticScheduler()
    scheduler.register_task(memory_consolidation_task, priority=Priority.HIGH)
    scheduler.start()
    
    # Later
    scheduler.stop()
"""

import asyncio
import datetime
import enum
import heapq
import logging
import threading
import time
import uuid
from collections.abc import Coroutine
from dataclasses import dataclass, field
from functools import total_ordering
from typing import Any, Callable, Optional, Union

# Configure logger
logger = logging.getLogger(__name__)


class Priority(enum.IntEnum):
    """Priority levels for scheduled tasks."""
    CRITICAL = 0
    HIGH = 1
    MEDIUM = 2
    LOW = 3
    BACKGROUND = 4


class TaskStatus(enum.Enum):
    """Status of a scheduled task."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@total_ordering
@dataclass(order=False)
class ScheduledTask:
    """
    Represents a task scheduled for execution in the lymphatic memory system.
    
    Tasks are ordered by scheduled_time and priority, with earlier times and
    higher priorities (lower numeric values) coming first.
    """
    task_id: str
    name: str
    callback: Union[Callable[..., Any], Coroutine[Any, Any, Any]]
    scheduled_time: float
    priority: Priority
    recurring: bool = False
    interval: Optional[float] = None
    last_run_time: Optional[float] = None
    next_run_time: Optional[float] = None
    status: TaskStatus = TaskStatus.PENDING
    args: tuple = field(default_factory=tuple)
    kwargs: dict[str, Any] = field(default_factory=dict)
    max_retries: int = 3
    retry_count: int = 0
    timeout: Optional[float] = None
    
    def __post_init__(self):
        """Initialize next_run_time if not set."""
        if self.next_run_time is None:
            self.next_run_time = self.scheduled_time
    
    def __eq__(self, other):
        if not isinstance(other, ScheduledTask):
            return NotImplemented
        return (self.next_run_time, self.priority) == (other.next_run_time, other.priority)
    
    def __lt__(self, other):
        if not isinstance(other, ScheduledTask):
            return NotImplemented
        return (self.next_run_time, self.priority) < (other.next_run_time, other.priority)
    
    def reschedule(self) -> bool:
        """
        Reschedule a recurring task for its next execution.
        
        Returns:
            bool: True if the task was rescheduled, False otherwise
        """
        if not self.recurring or self.interval is None:
            return False
        
        self.last_run_time = time.time()
        self.next_run_time = self.last_run_time + self.interval
        self.status = TaskStatus.PENDING
        self.retry_count = 0
        return True


class LymphaticScheduler:
    """
    Scheduler for lymphatic memory system tasks.
    
    This scheduler manages memory maintenance tasks including consolidation,
    cleanup, and optimization. It supports priority-based scheduling, recurring
    tasks, and adaptive scheduling based on system load.
    """
    
    def __init__(self, max_concurrent_tasks: int = 5, idle_threshold: float = 0.3):
        """
        Initialize the lymphatic scheduler.
        
        Args:
            max_concurrent_tasks: Maximum number of tasks to run concurrently
            idle_threshold: CPU utilization threshold below which to consider the system idle
        """
        self._task_queue: list[ScheduledTask] = []
        self._task_map: dict[str, ScheduledTask] = {}
        self._running_tasks: set[str] = set()
        self._lock = threading.RLock()
        self._event = threading.Event()
        self._scheduler_thread: Optional[threading.Thread] = None
        self._running = False
        self._max_concurrent_tasks = max_concurrent_tasks
        self._idle_threshold = idle_threshold
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        
        # Statistics and monitoring
        self._stats = {
            "tasks_completed": 0,
            "tasks_failed": 0,
            "avg_execution_time": 0.0,
            "last_idle_period": None,
        }
    
    def start(self) -> None:
        """Start the scheduler thread."""
        if self._running:
            logger.warning("Scheduler is already running")
            return
        
        self._running = True
        self._scheduler_thread = threading.Thread(
            target=self._scheduler_loop,
            name="LymphaticScheduler",
            daemon=True
        )
        self._scheduler_thread.start()
        logger.info("Lymphatic scheduler started")
    
    def stop(self) -> None:
        """Stop the scheduler thread."""
        if not self._running:
            logger.warning("Scheduler is not running")
            return
        
        self._running = False
        self._event.set()
        if self._scheduler_thread and self._scheduler_thread.is_alive():
            self._scheduler_thread.join(timeout=5.0)
        logger.info("Lymphatic scheduler stopped")
    
    def register_task(
        self,
        callback: Union[Callable[..., Any], Coroutine[Any, Any, Any]],
        name: str = None,
        scheduled_time: Optional[float] = None,
        priority: Priority = Priority.MEDIUM,
        recurring: bool = False,
        interval: Optional[float] = None,
        args: tuple = None,
        kwargs: dict[str, Any] = None,
        timeout: Optional[float] = None,
        max_retries: int = 3
    ) -> str:
        """
        Register a task with the scheduler.
        
        Args:
            callback: Function or coroutine to execute
            name: Name of the task (for logging and identification)
            scheduled_time: Time to execute the task (timestamp)
            priority: Priority level of the task
            recurring: Whether the task should recur
            interval: Interval between recurring executions (in seconds)
            args: Positional arguments to pass to the callback
            kwargs: Keyword arguments to pass to the callback
            timeout: Maximum execution time before considering the task failed
            max_retries: Maximum number of retry attempts for failed tasks
            
        Returns:
            str: Task ID that can be used to cancel or modify the task
        """
        if scheduled_time is None:
            scheduled_time = time.time()
        
        if name is None:
            name = callback.__name__
            
        task_id = str(uuid.uuid4())
        
        task = ScheduledTask(
            task_id=task_id,
            name=name,
            callback=callback,
            scheduled_time=scheduled_time,
            priority=priority,
            recurring=recurring,
            interval=interval,
            args=args or (),
            kwargs=kwargs or {},
            timeout=timeout,
            max_retries=max_retries
        )
        
        with self._lock:
            heapq.heappush(self._task_queue, task)
            self._task_map[task_id] = task
            self._event.set()  # Wake up the scheduler thread
        
        logger.debug(f"Registered task '{name}' with ID {task_id}")
        return task_id
    
    def cancel_task(self, task_id: str) -> bool:
        """
        Cancel a scheduled task.
        
        Args:
            task_id: ID of the task to cancel
            
        Returns:
            bool: True if the task was cancelled, False if not found
        """
        with self._lock:
            if task_id not in self._task_map:
                logger.warning(f"Attempted to cancel non-existent task: {task_id}")
                return False
            
            task = self._task_map[task_id]
            task.status = TaskStatus.CANCELLED
            
            # If the task is not currently running, remove it from the queue
            if task_id not in self._running_tasks:
                self._task_map.pop(task_id)
                # Rebuild the heap without the cancelled task
                self._task_queue = [t for t in self._task_queue if t.task_id != task_id]
                heapq.heapify(self._task_queue)
            
            logger.debug(f"Cancelled task '{task.name}' with ID {task_id}")
            return True
    
    def get_task_status(self, task_id: str) -> Optional[TaskStatus]:
        """
        Get the current status of a task.
        
        Args:
            task_id: ID of the task
            
        Returns:
            TaskStatus: Current status of the task, or None if not found
        """
        with self._lock:
            task = self._task_map.get(task_id)
            if task:
                return task.status
            return None
    
    def get_statistics(self) -> dict[str, Any]:
        """
        Get scheduler statistics.
        
        Returns:
            Dict: Dictionary containing scheduler statistics
        """
        with self._lock:
            return self._stats.copy()
    
    def _scheduler_loop(self) -> None:
        """Main scheduler loop that processes the task queue."""
        logger.debug("Scheduler loop started")
        
        # Create an event loop for this thread if needed
        try:
            self._loop = asyncio.get_event_loop()
        except RuntimeError:
            self._loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self._loop)
        
        while self._running:
            try:
                self._process_due_tasks()
                
                # Wait for the next task or until a new task is added
                with self._lock:
                    if not self._task_queue:
                        next_task_time = None
                    else:
                        next_task_time = self._task_queue[0].next_run_time
                
                if next_task_time is None:
                    # No tasks in queue, wait for a new task to be added
                    self._event.wait(timeout=1.0)
                else:
                    # Wait until the next task is due or a new task is added
                    wait_time = max(0, next_task_time - time.time())
                    self._event.wait(timeout=min(wait_time, 1.0))
                
                self._event.clear()
            except Exception as e:
                logger.error(f"Error in scheduler loop: {e}", exc_info=True)
                # Sleep briefly to avoid tight error loops
                time.sleep(1.0)
        
        logger.debug("Scheduler loop stopped")
    
    def _process_due_tasks(self) -> None:
        """Process all tasks that are due for execution."""
        current_time = time.time()
        tasks_to_execute = []
        
        with self._lock:
            # Check if we can run more tasks
            available_slots = self._max_concurrent_tasks - len(self._running_tasks)
            if available_slots <= 0:
                return
            
            # Extract tasks that are due
            while (self._task_queue and 
                   len(tasks_to_execute) < available_slots and 
                   self._task_queue[0].next_run_time <= current_time):
                task = heapq.heappop(self._task_queue)
                
                # Skip cancelled tasks
                if task.status == TaskStatus.CANCELLED:
                    self._task_map.pop(task.task_id, None)
                    continue
                
                tasks_to_execute.append(task)
                self._running_tasks.add(task.task_id)
                task.status = TaskStatus.RUNNING
        
        # Execute the tasks outside the lock
        for task in tasks_to_execute:
            self._execute_task(task)
    
    def _execute_task(self, task: ScheduledTask) -> None:
        """
        Execute a single task.
        
        Args:
            task: The task to execute
        """
        logger.debug(f"Executing task '{task.name}' (ID: {task.task_id})")
        start_time = time.time()
        
        try:
            # Handle both regular functions and coroutines
            if asyncio.iscoroutinefunction(task.callback):
                future = asyncio.run_coroutine_threadsafe(
                    task.callback(*task.args, **task.kwargs),
                    self._loop
                )
                
                # Wait for the coroutine to complete with timeout if specified
                future.result(task.timeout) if task.timeout else future.result()
            else:
                # Execute synchronous function
                if task.timeout:
                    # Use a separate thread with timeout for synchronous functions
                    result_container = []
                    
                    def run_with_result():
                        try:
                            result = task.callback(*task.args, **task.kwargs)
                            result_container.append(result)
                        except Exception as e:
                            result_container.append(e)
                    
                    thread = threading.Thread(target=run_with_result)
                    thread.daemon = True
                    thread.start()
                    thread.join(task.timeout)
                    
                    if thread.is_alive():
                        raise TimeoutError(f"Task '{task.name}' timed out after {task.timeout} seconds")
                    
                    if result_container and isinstance(result_container[0], Exception):
                        raise result_container[0]
                    
                    result_container[0] if result_container else None
                else:
                    # Execute directly without timeout
                    task.callback(*task.args, **task.kwargs)
            
            # Task completed successfully
            execution_time = time.time() - start_time
            self._handle_task_completion(task, execution_time)
            
        except Exception as e:
            # Task failed
            execution_time = time.time() - start_time
            self._handle_task_failure(task, e, execution_time)
    
    def _handle_task_completion(self, task: ScheduledTask, execution_time: float) -> None:
        """
        Handle successful task completion.
        
        Args:
            task: The completed task
            execution_time: Time taken to execute the task
        """
        with self._lock:
            self._running_tasks.discard(task.task_id)
            self._stats["tasks_completed"] += 1
            
            # Update average execution time
            avg = self._stats["avg_execution_time"]
            count = self._stats["tasks_completed"]
            self._stats["avg_execution_time"] = (avg * (count - 1) + execution_time) / count
            
            logger.debug(f"Task '{task.name}' completed in {execution_time:.3f}s")
            
            # Handle recurring tasks
            if task.recurring and task.interval:
                task.reschedule()
                heapq.heappush(self._task_queue, task)
            else:
                task.status = TaskStatus.COMPLETED
                self._task_map.pop(task.task_id, None)
    
    def _handle_task_failure(self, task: ScheduledTask, exception: Exception, execution_time: float) -> None:
        """
        Handle task failure.
        
        Args:
            task: The failed task
            exception: The exception that caused the failure
            execution_time: Time taken before the task failed
        """
        with self._lock:
            self._running_tasks.discard(task.task_id)
            self._stats["tasks_failed"] += 1
            
            logger.error(f"Task '{task.name}' failed after {execution_time:.3f}s: {exception}", exc_info=True)
            
            # Retry logic
            if task.retry_count < task.max_retries:
                task.retry_count += 1
                task.status = TaskStatus.PENDING
                # Exponential backoff for retries
                backoff = 2 ** task.retry_count
                task.next_run_time = time.time() + backoff
                
                logger.info(f"Retrying task '{task.name}' in {backoff}s (attempt {task.retry_count}/{task.max_retries})")
                heapq.heappush(self._task_queue, task)
            else:
                task.status = TaskStatus.FAILED
                
                # For recurring tasks, reschedule despite the failure
                if task.recurring and task.interval:
                    task.reschedule()
                    heapq.heappush(self._task_queue, task)
                else:
                    self._task_map.pop(task.task_id, None)
    
    def is_system_idle(self) -> bool:
        """
        Check if the system is currently idle.
        
        This can be used to determine if it's a good time to run
        resource-intensive maintenance tasks.
        
        Returns:
            bool: True if the system is idle, False otherwise
        """
        try:
            import psutil
            # Get CPU utilization over the last second
            cpu_percent = psutil.cpu_percent(interval=1.0)
            is_idle = cpu_percent < (self._idle_threshold * 100)
            
            if is_idle:
                self._stats["last_idle_period"] = datetime.datetime.now().isoformat()
            
            return is_idle
        except ImportError:
            logger.warning("psutil not available, cannot determine system idle state")
            # Default to assuming the system is not idle
            return False
    
    def schedule_during_idle(
        self,
        callback: Union[Callable[..., Any], Coroutine[Any, Any, Any]],
        name: str = None,
        priority: Priority = Priority.LOW,
        args: tuple = None,
        kwargs: dict[str, Any] = None,
        timeout: Optional[float] = None,
        max_retries: int = 3
    ) -> str:
        """
        Schedule a task to run during the next idle period.
        
        Args:
            callback: Function or coroutine to execute
            name: Name of the task
            priority: Priority level of the task
            args: Positional arguments to pass to the callback
            kwargs: Keyword arguments to pass to the callback
            timeout: Maximum execution time before considering the task failed
            max_retries: Maximum number of retry attempts for failed tasks
            
        Returns:
            str: Task ID that can be used to cancel or modify the task
        """
        if name is None:
            name = f"idle_{callback.__name__}"
        
        # Create a wrapper that checks for idle state before executing
        def idle_wrapper(*wrapper_args, **wrapper_kwargs):
            if not self.is_system_idle():
                # Reschedule for later if system is not idle
                logger.debug(f"System not idle, rescheduling task '{name}'")
                return False
            return callback(*wrapper_args, **wrapper_kwargs)
        
        # Schedule the wrapper to run soon, but with low priority
        return self.register_task(
            callback=idle_wrapper,
            name=name,
            scheduled_time=time.time() + 60,  # Check in a minute
            priority=priority,
            recurring=True,
            interval=300,  # Check every 5 minutes
            args=args,
            kwargs=kwargs,
            timeout=timeout,
            max_retries=max_retries
        )


# Example usage in doctest format
"""
>>> scheduler = LymphaticScheduler()
>>> scheduler.start()

>>> # Register a simple task
>>> def example_task(message):
...     print(f"Task executed: {message}")
...     return True
>>> task_id = scheduler.register_task(example_task, args=("Hello, world!",))

>>> # Register a recurring task
>>> def recurring_task():
...     print("This task runs every minute")
>>> recurring_id = scheduler.register_task(
...     recurring_task, 
...     recurring=True, 
...     interval=60.0
... )

>>> # Register a task to run during idle periods
>>> def maintenance_task():
...     print("Running maintenance during idle time")
>>> idle_task_id = scheduler.schedule_during_idle(maintenance_task)

>>> # Check task status
>>> status = scheduler.get_task_status(task_id)
>>> print(status)  # TaskStatus.PENDING or TaskStatus.RUNNING or TaskStatus.COMPLETED

>>> # Cancel a task
>>> scheduler.cancel_task(recurring_id)

>>> # Get scheduler statistics
>>> stats = scheduler.get_statistics()
>>> print(stats)

>>> # Stop the scheduler when done
>>> scheduler.stop()
"""

if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Example usage
    scheduler = LymphaticScheduler()
    scheduler.start()
    
    # Register a simple task
    def example_task(message):
        logger.info(f"Task executed: {message}")
        return True
    
    task_id = scheduler.register_task(
        example_task, 
        args=("Hello from the lymphatic scheduler!",)
    )
    
    # Keep the main thread alive for a bit
    try:
        time.sleep(5)
    except KeyboardInterrupt:
        pass
    finally:
        scheduler.stop()