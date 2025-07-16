from datetime import datetime
from enum import Enum
from typing import Optional, Dict, List, Any, Type, Union
from uuid import UUID, uuid4
from pydantic import BaseModel, Field

from app.types.output import Platform, Region, ContentType


class TaskStatus(str, Enum):
    """Task status enumeration"""
    PENDING = "pending"
    ASSIGNED = "assigned"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TaskPriority(str, Enum):
    """Task priority levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class ExpertRole(str, Enum):
    """Expert role types"""
    PLANNER = "planner"  # Jeff - Marketing Strategy Expert
    EXECUTOR = "executor"  # Monica - Content Generation Expert
    EVALUATOR = "evaluator"  # Henry - Content Review Expert


class TeamRole(str, Enum):
    """Team member roles"""
    OWNER = "owner"
    ADMIN = "admin"
    MEMBER = "member"
    OBSERVER = "observer"


# === Expert Instance and Assignment Types ===

class ExpertInstance(BaseModel):
    """Expert instance definition"""
    instance_id: str = Field(description="Unique instance identifier")
    expert_role: ExpertRole = Field(description="Expert role type")
    instance_name: str = Field(description="Human-readable instance name")
    status: str = Field(description="Current status: active, busy, offline")
    max_concurrent_tasks: int = Field(description="Maximum concurrent tasks", default=3)
    current_task_count: int = Field(description="Current active tasks", default=0)
    specializations: List[str] = Field(description="Expert specializations", default_factory=list)
    performance_metrics: Dict[str, float] = Field(description="Performance metrics", default_factory=dict)
    created_at: datetime = Field(description="Creation timestamp", default_factory=datetime.now)
    last_activity: datetime = Field(description="Last activity timestamp", default_factory=datetime.now)


class TaskAssignment(BaseModel):
    """Task assignment to expert instance"""
    assignment_id: str = Field(description="Assignment unique identifier", default_factory=lambda: str(uuid4()))
    task_id: str = Field(description="Task identifier")
    expert_instance_id: str = Field(description="Assigned expert instance")
    assigned_by: str = Field(description="Who assigned the task")
    assigned_at: datetime = Field(description="Assignment timestamp", default_factory=datetime.now)
    started_at: Optional[datetime] = Field(description="Start timestamp", default=None)
    completed_at: Optional[datetime] = Field(description="Completion timestamp", default=None)
    estimated_duration: Optional[int] = Field(description="Estimated duration in minutes", default=None)
    actual_duration: Optional[int] = Field(description="Actual duration in minutes", default=None)


# === Task Definition Types ===

class TaskDependency(BaseModel):
    """Task dependency definition"""
    dependent_task_id: str = Field(description="Task that depends on another")
    prerequisite_task_id: str = Field(description="Prerequisite task")
    dependency_type: str = Field(description="Type: blocking, soft, optional")


class TaskMetadata(BaseModel):
    """Task metadata"""
    tags: List[str] = Field(description="Task tags", default_factory=list)
    category: str = Field(description="Task category")
    subcategory: Optional[str] = Field(description="Task subcategory", default=None)
    estimated_complexity: float = Field(description="Complexity score 1-10", default=5.0)
    required_skills: List[str] = Field(description="Required skills", default_factory=list)
    context_data: Dict[str, Any] = Field(description="Additional context", default_factory=dict)


class BlackboardTask(BaseModel):
    """Comprehensive task definition for BlackBoard"""
    task_id: str = Field(description="Unique task identifier", default_factory=lambda: str(uuid4()))
    team_id: str = Field(description="Team identifier")
    parent_task_id: Optional[str] = Field(description="Parent task ID for subtasks", default=None)
    
    # Task basic information
    title: str = Field(description="Task title")
    description: str = Field(description="Detailed task description")
    goal: str = Field(description="Task goal/objective")
    
    # Task status and lifecycle
    status: TaskStatus = Field(description="Current task status", default=TaskStatus.PENDING)
    priority: TaskPriority = Field(description="Task priority", default=TaskPriority.MEDIUM)
    
    # Assignment and execution
    required_expert_role: ExpertRole = Field(description="Required expert role")
    assignment: Optional[TaskAssignment] = Field(description="Current assignment", default=None)
    
    # Platform and content specific
    target_platforms: List[Platform] = Field(description="Target platforms", default_factory=list)
    target_regions: List[Region] = Field(description="Target regions", default_factory=list)
    content_types: List[ContentType] = Field(description="Content types", default_factory=list)
    
    # Dependencies and workflow
    dependencies: List[TaskDependency] = Field(description="Task dependencies", default_factory=list)
    subtasks: List[str] = Field(description="Subtask IDs", default_factory=list)
    
    # Timing and deadlines
    created_at: datetime = Field(description="Creation timestamp", default_factory=datetime.now)
    updated_at: datetime = Field(description="Last update timestamp", default_factory=datetime.now)
    due_date: Optional[datetime] = Field(description="Due date", default=None)
    
    # Results and output
    input_data: Dict[str, Any] = Field(description="Task input data", default_factory=dict)
    output_data: Dict[str, Any] = Field(description="Task output data", default_factory=dict)
    execution_log: List[str] = Field(description="Execution log", default_factory=list)
    error_messages: List[str] = Field(description="Error messages", default_factory=list)
    
    # Metadata
    metadata: TaskMetadata = Field(description="Task metadata", default_factory=TaskMetadata)


# === Team and Multi-tenant Types ===

class TeamMember(BaseModel):
    """Team member definition"""
    user_id: str = Field(description="User identifier")
    username: str = Field(description="Username")
    role: TeamRole = Field(description="Team role")
    permissions: List[str] = Field(description="Specific permissions", default_factory=list)
    joined_at: datetime = Field(description="Join timestamp", default_factory=datetime.now)
    last_active: datetime = Field(description="Last active timestamp", default_factory=datetime.now)


class TeamConfiguration(BaseModel):
    """Team configuration for expert instances"""
    max_jeff_instances: int = Field(description="Maximum Jeff instances", default=2)
    max_monica_instances: int = Field(description="Maximum Monica instances", default=3)
    max_henry_instances: int = Field(description="Maximum Henry instances", default=2)
    auto_scaling_enabled: bool = Field(description="Enable auto scaling", default=True)
    task_queue_limit: int = Field(description="Maximum tasks in queue", default=100)
    concurrent_task_limit: int = Field(description="Maximum concurrent tasks", default=10)


class Team(BaseModel):
    """Multi-tenant team definition"""
    team_id: str = Field(description="Unique team identifier", default_factory=lambda: str(uuid4()))
    team_name: str = Field(description="Team name")
    organization_id: str = Field(description="Organization identifier")
    
    # Team membership
    members: List[TeamMember] = Field(description="Team members", default_factory=list)
    owner_id: str = Field(description="Team owner user ID")
    
    # Expert instances
    expert_instances: List[ExpertInstance] = Field(description="Expert instances", default_factory=list)
    configuration: TeamConfiguration = Field(description="Team configuration", default_factory=TeamConfiguration)
    
    # Team metadata
    created_at: datetime = Field(description="Creation timestamp", default_factory=datetime.now)
    updated_at: datetime = Field(description="Last update timestamp", default_factory=datetime.now)
    is_active: bool = Field(description="Team active status", default=True)
    
    # Usage metrics
    total_tasks_completed: int = Field(description="Total completed tasks", default=0)
    total_content_generated: int = Field(description="Total content pieces", default=0)
    team_performance_score: float = Field(description="Team performance score", default=0.0)


# === BlackBoard State and Events ===

class TaskEvent(BaseModel):
    """Task lifecycle events"""
    event_id: str = Field(description="Event identifier", default_factory=lambda: str(uuid4()))
    task_id: str = Field(description="Task identifier")
    event_type: str = Field(description="Event type: created, assigned, started, completed, failed")
    event_data: Dict[str, Any] = Field(description="Event data", default_factory=dict)
    triggered_by: str = Field(description="Who triggered the event")
    timestamp: datetime = Field(description="Event timestamp", default_factory=datetime.now)


class BlackboardState(BaseModel):
    """Current state of the BlackBoard"""
    team_id: str = Field(description="Team identifier")
    
    # Task collections
    pending_tasks: List[str] = Field(description="Pending task IDs", default_factory=list)
    assigned_tasks: List[str] = Field(description="Assigned task IDs", default_factory=list)
    in_progress_tasks: List[str] = Field(description="In-progress task IDs", default_factory=list)
    completed_tasks: List[str] = Field(description="Completed task IDs", default_factory=list)
    failed_tasks: List[str] = Field(description="Failed task IDs", default_factory=list)
    
    # Expert instance status
    expert_status: Dict[str, str] = Field(description="Expert instance statuses", default_factory=dict)
    task_assignments: Dict[str, str] = Field(description="Task to expert mappings", default_factory=dict)
    
    # Statistics
    total_tasks: int = Field(description="Total tasks", default=0)
    completion_rate: float = Field(description="Completion rate", default=0.0)
    average_duration: float = Field(description="Average task duration", default=0.0)
    
    # Timestamps
    last_updated: datetime = Field(description="Last update timestamp", default_factory=datetime.now)


# === Notification and Communication Types ===

class TaskNotification(BaseModel):
    """Task-related notifications"""
    notification_id: str = Field(description="Notification identifier", default_factory=lambda: str(uuid4()))
    team_id: str = Field(description="Team identifier")
    task_id: str = Field(description="Related task ID")
    notification_type: str = Field(description="Type: assignment, completion, failure, deadline")
    title: str = Field(description="Notification title")
    message: str = Field(description="Notification message")
    recipients: List[str] = Field(description="Recipient user IDs", default_factory=list)
    priority: TaskPriority = Field(description="Notification priority", default=TaskPriority.MEDIUM)
    created_at: datetime = Field(description="Creation timestamp", default_factory=datetime.now)
    read_by: List[str] = Field(description="Users who read notification", default_factory=list)


class CollaborationComment(BaseModel):
    """Task collaboration comments"""
    comment_id: str = Field(description="Comment identifier", default_factory=lambda: str(uuid4()))
    task_id: str = Field(description="Related task ID")
    author_id: str = Field(description="Comment author")
    content: str = Field(description="Comment content")
    comment_type: str = Field(description="Type: question, suggestion, note, approval")
    parent_comment_id: Optional[str] = Field(description="Parent comment for replies", default=None)
    created_at: datetime = Field(description="Creation timestamp", default_factory=datetime.now)
    updated_at: Optional[datetime] = Field(description="Update timestamp", default=None)
    is_resolved: bool = Field(description="Whether comment is resolved", default=False)


# === Search and Filter Types ===

class TaskFilter(BaseModel):
    """Task filtering criteria"""
    status: Optional[List[TaskStatus]] = Field(description="Filter by status", default=None)
    priority: Optional[List[TaskPriority]] = Field(description="Filter by priority", default=None)
    expert_role: Optional[List[ExpertRole]] = Field(description="Filter by expert role", default=None)
    assigned_to: Optional[List[str]] = Field(description="Filter by assignee", default=None)
    platforms: Optional[List[Platform]] = Field(description="Filter by platforms", default=None)
    regions: Optional[List[Region]] = Field(description="Filter by regions", default=None)
    tags: Optional[List[str]] = Field(description="Filter by tags", default=None)
    date_range: Optional[Dict[str, datetime]] = Field(description="Date range filter", default=None)


class TaskSearchCriteria(BaseModel):
    """Task search criteria"""
    query: Optional[str] = Field(description="Text search query", default=None)
    filters: TaskFilter = Field(description="Filter criteria", default_factory=TaskFilter)
    sort_by: str = Field(description="Sort field", default="created_at")
    sort_order: str = Field(description="Sort order: asc, desc", default="desc")
    limit: int = Field(description="Result limit", default=50)
    offset: int = Field(description="Result offset", default=0) 