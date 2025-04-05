"""
Memory consolidation utilities for the NCA system.

This module provides utilities for the memory consolidation process,
complementing the functionality in memory_consolidation.py.
"""

import logging
from datetime import datetime, timedelta
from typing import Any, Callable, Optional

# Set up logger
logger = logging.getLogger(__name__)

class ConsolidationTask:
    """Represents a consolidation task to be scheduled and executed."""
    
    def __init__(self, task_id: str, memory_ids: list[str], 
                 task_type: str = "standard", 
                 priority: int = 1,
                 scheduled_time: Optional[datetime] = None):
        """
        Initialize a consolidation task.
        
        Args:
            task_id: Unique identifier for the task
            memory_ids: List of memory IDs to consolidate
            task_type: Type of consolidation task
            priority: Task priority (higher numbers = higher priority)
            scheduled_time: When the task should be executed
        """
        self.task_id = task_id
        self.memory_ids = memory_ids
        self.task_type = task_type
        self.priority = priority
        self.scheduled_time = scheduled_time or datetime.now()
        self.status = "pending"
        self.result: Optional[dict[str, Any]] = None
        self.created_at = datetime.now()
        self.executed_at: Optional[datetime] = None
        
    def to_dict(self) -> dict[str, Any]:
        """Convert the task to a dictionary representation."""
        return {
            "task_id": self.task_id,
            "memory_ids": self.memory_ids,
            "task_type": self.task_type,
            "priority": self.priority,
            "scheduled_time": self.scheduled_time.isoformat(),
            "status": self.status,
            "result": self.result,
            "created_at": self.created_at.isoformat(),
            "executed_at": self.executed_at.isoformat() if self.executed_at else None
        }
        
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> 'ConsolidationTask':
        """Create a consolidation task from a dictionary."""
        task = cls(
            task_id=data["task_id"],
            memory_ids=data["memory_ids"],
            task_type=data.get("task_type", "standard"),
            priority=data.get("priority", 1),
            scheduled_time=datetime.fromisoformat(data["scheduled_time"])
        )
        task.status = data.get("status", "pending")
        task.result = data.get("result")
        task.created_at = datetime.fromisoformat(data["created_at"])
        if data.get("executed_at"):
            task.executed_at = datetime.fromisoformat(data["executed_at"])
        return task


class ConsolidationScheduler:
    """Schedules and manages memory consolidation tasks."""
    
    def __init__(self):
        """Initialize the consolidation scheduler."""
        self.tasks: dict[str, ConsolidationTask] = {}
        self.callbacks: dict[str, Callable] = {}
        
    def schedule_task(self, task: ConsolidationTask) -> str:
        """
        Schedule a consolidation task.
        
        Args:
            task: The task to schedule
            
        Returns:
            Task ID
        """
        self.tasks[task.task_id] = task
        logger.info(f"Scheduled consolidation task {task.task_id} for {task.scheduled_time}")
        return task.task_id
        
    def get_pending_tasks(self, current_time: Optional[datetime] = None) -> list[ConsolidationTask]:
        """
        Get all pending tasks that are due for execution.
        
        Args:
            current_time: Current time reference (defaults to now)
            
        Returns:
            List of due tasks, sorted by priority
        """
        if current_time is None:
            current_time = datetime.now()
            
        due_tasks = [
            task for task in self.tasks.values()
            if task.status == "pending" and task.scheduled_time <= current_time
        ]
        
        return sorted(due_tasks, key=lambda t: t.priority, reverse=True)
        
    def register_callback(self, task_type: str, callback: Callable) -> None:
        """
        Register a callback function for a specific task type.
        
        Args:
            task_type: Type of tasks to assign the callback
            callback: Function to call when tasks of this type are due
        """
        self.callbacks[task_type] = callback
        logger.info(f"Registered callback for task type: {task_type}")
        
    def process_due_tasks(self, current_time: Optional[datetime] = None) -> int:
        """
        Process all due tasks.
        
        Args:
            current_time: Current time reference (defaults to now)
            
        Returns:
            Number of tasks processed
        """
        due_tasks = self.get_pending_tasks(current_time)
        processed_count = 0
        
        for task in due_tasks:
            callback = self.callbacks.get(task.task_type)
            if callback:
                try:
                    task.status = "processing"
                    result = callback(task)
                    task.result = result
                    task.status = "completed"
                    task.executed_at = datetime.now()
                    logger.info(f"Completed task {task.task_id}")
                    processed_count += 1
                except Exception as e:
                    task.status = "failed"
                    task.result = {"error": str(e)}
                    logger.error(f"Error processing task {task.task_id}: {str(e)}")
            else:
                logger.warning(f"No callback registered for task type: {task.task_type}")
                task.status = "skipped"
                
        return processed_count


# Create a singleton instance
scheduler = ConsolidationScheduler()

def schedule_consolidation(memory_ids: list[str], delay_minutes: int = 0, 
                          task_type: str = "standard", priority: int = 1) -> str:
    """
    Schedule a memory consolidation task.
    
    Args:
        memory_ids: List of memory IDs to consolidate
        delay_minutes: Minutes to delay execution
        task_type: Type of consolidation task
        priority: Task priority
        
    Returns:
        Task ID
    """
    task_id = f"consolidation_{datetime.now().strftime('%Y%m%d%H%M%S')}_{len(memory_ids)}"
    scheduled_time = datetime.now() + timedelta(minutes=delay_minutes)
    
    task = ConsolidationTask(
        task_id=task_id,
        memory_ids=memory_ids,
        task_type=task_type,
        priority=priority,
        scheduled_time=scheduled_time
    )
    
    return scheduler.schedule_task(task)


def process_pending_consolidations() -> int:
    """
    Process all pending consolidation tasks.
    
    Returns:
        Number of tasks processed
    """
    return scheduler.process_due_tasks() 