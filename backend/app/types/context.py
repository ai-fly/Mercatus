from dataclasses import dataclass
from typing import Optional, Dict, Any

from app.types.output import AgentExecutorResultItem as TaskItem


@dataclass
class AppContext:
    """Application context for configuration and shared state"""
    config: Optional[Dict[str, Any]] = None
    """Application configuration"""
    
    session_id: Optional[str] = None
    """Current session identifier"""
    
    user_id: Optional[str] = None
    """Current user identifier"""
    
    debug: bool = False
    """Debug mode flag"""


@dataclass
class ExecutorContext():
    goal: str
    """User's goal"""
    
    tasks: list[TaskItem]
    """All tasks"""

    finished: bool
    """Whether the task is completed"""

    current_task: TaskItem
    """The task currently being executed"""

    execution_history: list[str]
    """Execution history"""
    