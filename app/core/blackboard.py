import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Type, Any
from uuid import uuid4

from app.types.blackboard import (
    BlackboardTask, TaskStatus, TaskPriority, ExpertRole, TeamRole,
    ExpertInstance, TaskAssignment, Team, TeamMember, TeamConfiguration,
    BlackboardState, TaskEvent, TaskNotification, CollaborationComment,
    TaskFilter, TaskSearchCriteria, TaskDependency
)
from app.types.output import Platform, Region, ContentType
from app.clients.redis_client import redis_client_instance
from app.config import settings
from app.utils.logging import get_business_logger, get_performance_logger


class BlackBoard:
    """
    Multi-tenant BlackBoard system for team collaboration and task management.
    Provides shared visibility of all tasks across team members with assignment to expert instances.
    Now uses hybrid storage: PostgreSQL for persistence + Redis for caching.
    """
    
    def __init__(self, team_id: str, hybrid_storage_service=None):
        """Initialize BlackBoard for a specific team"""
        self.team_id = team_id
        self.redis_client = redis_client_instance.get_redis_client()
        self.logger = logging.getLogger(f"BlackBoard-{team_id}")
        self.business_logger = get_business_logger()
        self.performance_logger = get_performance_logger()
        
        # 混合存储服务
        self.hybrid_storage = hybrid_storage_service
        
        # Redis key prefixes (用于缓存和实时状态)
        self.task_prefix = f"blackboard:{team_id}:task"
        self.state_key = f"blackboard:{team_id}:state"
        self.expert_prefix = f"blackboard:{team_id}:expert"
        self.assignment_prefix = f"blackboard:{team_id}:assignment"
        self.event_prefix = f"blackboard:{team_id}:event"
        self.notification_prefix = f"blackboard:{team_id}:notification"
        self.comment_prefix = f"blackboard:{team_id}:comment"
        
        self.logger.info(f"BlackBoard initialized for team {team_id} with hybrid storage")
    
    # === Task Management (Hybrid Storage) ===
    
    async def create_task(
        self,
        title: str,
        description: str,
        goal: str,
        required_expert_role: ExpertRole,
        creator_id: str,
        priority: TaskPriority = TaskPriority.MEDIUM,
        target_platforms: List[Platform] = None,
        target_regions: List[Region] = None,
        content_types: List[ContentType] = None,
        due_date: Optional[datetime] = None,
        dependencies: List[TaskDependency] = None,
        metadata: Dict = None,
        parent_task_id: Optional[str] = None
    ) -> BlackboardTask:

        """Create a new task with hybrid storage"""
        
        with self.performance_logger.time_operation(
            "blackboard_create_task",
            team_id=self.team_id,
            expert_role=required_expert_role.value
        ):
            # 记录任务创建开始
            self.logger.debug(
                f"Creating task: {title} for expert role {required_expert_role.value}",
                extra={
                    'team_id': self.team_id,
                    'user_id': creator_id,
                    'expert_role': required_expert_role.value,
                    'priority': priority.value
                }
            )
            
            # 准备任务数据
            task_data = {
                "task_id": str(uuid4()),
                "team_id": self.team_id,
                "title": title,
                "description": description,
                "goal": goal,
                "required_expert_role": required_expert_role.value,
                "priority": priority.value,
                "target_platforms": [p.value for p in (target_platforms or [])],
                "target_regions": [r.value for r in (target_regions or [])],
                "content_types": [c.value for c in (content_types or [])],
                "due_date": due_date,
                "dependencies": [dep.model_dump() for dep in (dependencies or [])],
                "parent_task_id": parent_task_id,
                "creator_id": creator_id,
                "metadata": metadata or {}
            }
            
            # 使用混合存储创建任务
            if self.hybrid_storage:
                result = await self.hybrid_storage.create_task(task_data)
                if result["status"] == "success":
                    # 创建 BlackboardTask 对象用于返回
                    task = BlackboardTask(**result["task"])
                    
                    # 更新 Redis 状态
                    await self._add_task_to_state(task.task_id, TaskStatus.PENDING)
                    
                    self.logger.info(
                        f"Task created successfully with hybrid storage: {task.task_id}",
                        extra={
                            'team_id': self.team_id,
                            'task_id': task.task_id,
                            'expert_role': required_expert_role.value,
                            'storage_type': 'hybrid'
                        }
                    )
                    
                    return task
                else:
                    raise Exception(f"Failed to create task: {result['message']}")
            else:
                # 回退到纯 Redis 存储
                return await self._create_task_redis_only(task_data)
    
    async def assign_task(
        self, 
        task_id: str, 
        expert_instance_id: str, 
        assigned_by: str,
        estimated_duration: Optional[int] = None
    ) -> bool:
        """Assign a task to a specific expert instance"""
        
        with self.performance_logger.time_operation(
            "assign_task",
            team_id=self.team_id,
            task_id=task_id,
            expert_instance_id=expert_instance_id
        ):
            self.logger.debug(
                f"Attempting to assign task {task_id} to expert {expert_instance_id}",
                extra={
                    'task_id': task_id,
                    'team_id': self.team_id,
                    'expert_instance_id': expert_instance_id,
                    'user_id': assigned_by
                }
            )
            
            # Get task and expert instance
            task = await self.get_task(task_id)
            if not task:
                self.logger.error(
                    f"Task {task_id} not found",
                    extra={'task_id': task_id, 'team_id': self.team_id, 'user_id': assigned_by}
                )
                return False
            
            expert_instance = await self.get_expert_instance(expert_instance_id)
            if not expert_instance:
                self.logger.error(
                    f"Expert instance {expert_instance_id} not found",
                    extra={
                        'task_id': task_id,
                        'team_id': self.team_id,
                        'expert_instance_id': expert_instance_id,
                        'user_id': assigned_by
                    }
                )
                return False
            
            # Check if expert can handle the task
            if expert_instance.expert_role != task.required_expert_role:
                self.logger.warning(
                    f"Expert role mismatch: {expert_instance.expert_role} != {task.required_expert_role}",
                    extra={
                        'task_id': task_id,
                        'team_id': self.team_id,
                        'expert_instance_id': expert_instance_id,
                        'expected_role': task.required_expert_role.value,
                        'actual_role': expert_instance.expert_role.value,
                        'user_id': assigned_by
                    }
                )
                return False
            
            # Check expert capacity
            if expert_instance.current_task_count >= expert_instance.max_concurrent_tasks:
                self.logger.warning(
                    f"Expert instance {expert_instance_id} at capacity ({expert_instance.current_task_count}/{expert_instance.max_concurrent_tasks})",
                    extra={
                        'task_id': task_id,
                        'team_id': self.team_id,
                        'expert_instance_id': expert_instance_id,
                        'current_load': expert_instance.current_task_count,
                        'max_capacity': expert_instance.max_concurrent_tasks,
                        'user_id': assigned_by
                    }
                )
                return False
            
            # Create assignment
            assignment = TaskAssignment(
                task_id=task_id,
                expert_instance_id=expert_instance_id,
                assigned_by=assigned_by,
                estimated_duration=estimated_duration
            )
            
            # Update task
            task.assignment = assignment
            task.status = TaskStatus.ASSIGNED
            task.updated_at = datetime.now()
            
            # Update expert instance
            expert_instance.current_task_count += 1
            expert_instance.last_activity = datetime.now()
            
            # Store updates
            await self._store_task(task)
            await self._store_expert_instance(expert_instance)
            
            # Update state
            await self._move_task_in_state(task_id, TaskStatus.PENDING, TaskStatus.ASSIGNED)
            
            # Create event
            await self._create_event(
                task_id,
                "task_assigned",
                {"expert_instance_id": expert_instance_id, "assigned_by": assigned_by},
                assigned_by
            )
            
            # Send notifications
            await self._notify_team_members(
                task_id,
                "task_assigned",
                f"Task assigned: {task.title}",
                f"Task assigned to {expert_instance.instance_name}",
                [assigned_by]
            )
            
            # 使用业务日志记录器
            self.business_logger.log_task_assigned(
                task_id, expert_instance_id, self.team_id, assigned_by
            )
            
            self.logger.info(
                f"Assigned task {task_id} to expert {expert_instance_id}",
                extra={
                    'task_id': task_id,
                    'team_id': self.team_id,
                    'expert_instance_id': expert_instance_id,
                    'expert_type': expert_instance.expert_role.value,
                    'expert_load': expert_instance.current_task_count,
                    'user_id': assigned_by,
                    'estimated_duration': estimated_duration
                }
            )
            
            return True
    
    async def start_task(self, task_id: str, started_by: str) -> bool:
        """Mark a task as started"""
        
        with self.performance_logger.time_operation(
            "start_task",
            team_id=self.team_id,
            task_id=task_id
        ):
            task = await self.get_task(task_id)
            if not task or task.status != TaskStatus.ASSIGNED:
                self.logger.warning(
                    f"Cannot start task {task_id}: task not found or not assigned",
                    extra={
                        'task_id': task_id,
                        'team_id': self.team_id,
                        'current_status': task.status.value if task else 'NOT_FOUND',
                        'user_id': started_by
                    }
                )
                return False
            
            # Update task
            task.status = TaskStatus.IN_PROGRESS
            task.updated_at = datetime.now()
            if task.assignment:
                task.assignment.started_at = datetime.now()
            
            # Store task
            await self._store_task(task)
            
            # Update state
            await self._move_task_in_state(task_id, TaskStatus.ASSIGNED, TaskStatus.IN_PROGRESS)
            
            # Create event
            await self._create_event(
                task_id,
                "task_started",
                {"started_by": started_by},
                started_by
            )
            
            # 记录任务执行开始
            expert_type = task.assignment.expert_instance_id if task.assignment else "unknown"
            self.business_logger.log_task_execution_start(
                task_id, expert_type, self.team_id
            )
            
            self.logger.info(
                f"Started task {task_id}",
                extra={
                    'task_id': task_id,
                    'team_id': self.team_id,
                    'expert_instance_id': task.assignment.expert_instance_id if task.assignment else None,
                    'user_id': started_by,
                    'start_time': task.assignment.started_at.isoformat() if task.assignment and task.assignment.started_at else None
                }
            )
            
            return True
    
    async def complete_task(
        self,
        task_id: str,
        completed_by: str,
        output_data: Dict = None,
        execution_log: List[str] = None
    ) -> bool:
        """Mark a task as completed"""
        
        with self.performance_logger.time_operation(
            "complete_task",
            team_id=self.team_id,
            task_id=task_id
        ):
            task = await self.get_task(task_id)
            if not task or task.status != TaskStatus.IN_PROGRESS:
                self.logger.warning(
                    f"Cannot complete task {task_id}: task not found or not in progress",
                    extra={
                        'task_id': task_id,
                        'team_id': self.team_id,
                        'current_status': task.status.value if task else 'NOT_FOUND',
                        'user_id': completed_by
                    }
                )
                return False
            
            # 计算执行时间
            execution_time = 0.0
            if task.assignment and task.assignment.started_at:
                execution_time = (datetime.now() - task.assignment.started_at).total_seconds()
                self.logger.debug(f"Task {task_id} execution time: {execution_time:.2f} seconds")
            
            # Update task
            task.status = TaskStatus.COMPLETED
            task.updated_at = datetime.now()
            if output_data:
                task.output_data.update(output_data)
                self.logger.debug(f"Added output data to task {task_id}: {list(output_data.keys())}")
            if execution_log:
                task.execution_log.extend(execution_log)
                self.logger.debug(f"Added {len(execution_log)} log entries to task {task_id}")
            
            if task.assignment:
                task.assignment.completed_at = datetime.now()
                if task.assignment.started_at:
                    duration = (task.assignment.completed_at - task.assignment.started_at).total_seconds() / 60
                    task.assignment.actual_duration = int(duration)
            
            # Update expert instance
            if task.assignment:
                expert_instance = await self.get_expert_instance(task.assignment.expert_instance_id)
                if expert_instance:
                    expert_instance.current_task_count -= 1
                    expert_instance.last_activity = datetime.now()
                    # Update performance metrics
                    if "completed_tasks" not in expert_instance.performance_metrics:
                        expert_instance.performance_metrics["completed_tasks"] = 0
                    expert_instance.performance_metrics["completed_tasks"] += 1
                    await self._store_expert_instance(expert_instance)
                    
                    self.logger.debug(
                        f"Updated expert {task.assignment.expert_instance_id} metrics",
                        extra={
                            'expert_instance_id': task.assignment.expert_instance_id,
                            'current_load': expert_instance.current_task_count,
                            'completed_tasks': expert_instance.performance_metrics["completed_tasks"]
                        }
                    )
            
            # Store task
            await self._store_task(task)
            
            # Update state
            await self._move_task_in_state(task_id, TaskStatus.IN_PROGRESS, TaskStatus.COMPLETED)
            
            # Create event
            await self._create_event(
                task_id,
                "task_completed",
                {"completed_by": completed_by, "execution_time": execution_time},
                completed_by
            )
            
            # Send notifications
            await self._notify_team_members(
                task_id,
                "task_completed",
                f"Task completed: {task.title}",
                f"Task has been successfully completed",
                [completed_by]
            )
            
            # 记录任务执行完成
            expert_type = expert_instance.expert_role.value if task.assignment and expert_instance else "unknown"
            self.business_logger.log_task_execution_complete(
                task_id, expert_type, execution_time, self.team_id
            )
            
            self.logger.info(
                f"Completed task {task_id}",
                extra={
                    'task_id': task_id,
                    'team_id': self.team_id,
                    'expert_instance_id': task.assignment.expert_instance_id if task.assignment else None,
                    'expert_type': expert_type,
                    'execution_time': execution_time,
                    'user_id': completed_by,
                    'output_data_keys': list(output_data.keys()) if output_data else [],
                    'log_entries_count': len(execution_log) if execution_log else 0
                }
            )
            
            return True
    
    async def fail_task(
        self,
        task_id: str,
        failed_by: str,
        error_messages: List[str] = None,
        retry_possible: bool = True
    ) -> bool:
        """Mark a task as failed"""
        
        with self.performance_logger.time_operation(
            "fail_task",
            team_id=self.team_id,
            task_id=task_id
        ):
            task = await self.get_task(task_id)
            if not task:
                self.logger.error(
                    f"Cannot fail task {task_id}: task not found",
                    extra={'task_id': task_id, 'team_id': self.team_id, 'user_id': failed_by}
                )
                return False
            
            # 计算执行时间
            execution_time = 0.0
            if task.assignment and task.assignment.started_at:
                execution_time = (datetime.now() - task.assignment.started_at).total_seconds()
            
            # Update task
            task.status = TaskStatus.FAILED
            task.updated_at = datetime.now()
            if error_messages:
                task.error_messages.extend(error_messages)
                self.logger.error(
                    f"Task {task_id} failed with errors: {'; '.join(error_messages)}",
                    extra={
                        'task_id': task_id,
                        'team_id': self.team_id,
                        'error_count': len(error_messages),
                        'user_id': failed_by
                    }
                )
            
            # Update expert instance
            if task.assignment:
                expert_instance = await self.get_expert_instance(task.assignment.expert_instance_id)
                if expert_instance:
                    expert_instance.current_task_count -= 1
                    expert_instance.last_activity = datetime.now()
                    # Update performance metrics
                    if "failed_tasks" not in expert_instance.performance_metrics:
                        expert_instance.performance_metrics["failed_tasks"] = 0
                    expert_instance.performance_metrics["failed_tasks"] += 1
                    await self._store_expert_instance(expert_instance)
                    
                    self.logger.warning(
                        f"Expert {task.assignment.expert_instance_id} failed task",
                        extra={
                            'expert_instance_id': task.assignment.expert_instance_id,
                            'failed_tasks': expert_instance.performance_metrics["failed_tasks"],
                            'current_load': expert_instance.current_task_count
                        }
                    )
            
            # Store task
            await self._store_task(task)
            
            # Update state
            current_status = TaskStatus.IN_PROGRESS if task.assignment else TaskStatus.ASSIGNED
            await self._move_task_in_state(task_id, current_status, TaskStatus.FAILED)
            
            # Create event
            await self._create_event(
                task_id,
                "task_failed",
                {
                    "failed_by": failed_by, 
                    "retry_possible": retry_possible,
                    "execution_time": execution_time,
                    "error_count": len(error_messages) if error_messages else 0
                },
                failed_by
            )
            
            # Send notifications
            await self._notify_team_members(
                task_id,
                "task_failed",
                f"Task failed: {task.title}",
                f"Task has failed. Retry possible: {retry_possible}",
                [failed_by]
            )
            
            self.logger.warning(
                f"Failed task {task_id}",
                extra={
                    'task_id': task_id,
                    'team_id': self.team_id,
                    'expert_instance_id': task.assignment.expert_instance_id if task.assignment else None,
                    'execution_time': execution_time,
                    'retry_possible': retry_possible,
                    'user_id': failed_by,
                    'error_messages': error_messages or []
                }
            )
            
            return True
    
    # === Expert Instance Management (Hybrid Storage) ===
    
    async def register_expert_instance(
        self,
        expert_role: ExpertRole,
        instance_name: str,
        max_concurrent_tasks: int = 3,
        specializations: List[str] = None
    ) -> ExpertInstance:
        """Register a new expert instance"""
        
        instance = ExpertInstance(
            instance_id=str(uuid4()),
            expert_role=expert_role,
            instance_name=instance_name,
            status="active",
            max_concurrent_tasks=max_concurrent_tasks,
            specializations=specializations or []
        )
        
        await self._store_expert_instance(instance)
        
        self.logger.info(f"Registered expert instance {instance.instance_id}: {instance_name}")
        return instance
    
    async def create_expert_instance(self, expert_data: Dict[str, Any]) -> ExpertInstance:
        """Create expert instance with hybrid storage"""
        
        try:
            if self.hybrid_storage:
                result = await self.hybrid_storage.create_expert_instance(expert_data)
                if result["status"] == "success":
                    return ExpertInstance(**result["expert"])
                else:
                    raise Exception(f"Failed to create expert instance: {result['message']}")
            else:
                # 回退到纯 Redis 存储
                return await self._create_expert_instance_redis_only(expert_data)
                
        except Exception as e:
            self.logger.error(f"Failed to create expert instance: {str(e)}")
            raise
    
    async def get_available_experts(self, required_role: ExpertRole) -> List[ExpertInstance]:
        """Get available expert instances for a specific role"""
        
        all_experts = await self.get_team_experts() # Use hybrid storage
        available_experts = []
        
        for expert in all_experts:
            if (expert.expert_role == required_role and
                expert.status == "active" and
                expert.current_task_count < expert.max_concurrent_tasks):
                available_experts.append(expert)
        
        # Sort by current load (ascending)
        available_experts.sort(key=lambda x: x.current_task_count)
        return available_experts
    
    async def get_expert_instance(self, instance_id: str) -> Optional[ExpertInstance]:
        """Get expert instance with hybrid storage"""
        
        try:
            if self.hybrid_storage:
                expert_data = await self.hybrid_storage.get_expert_instance(instance_id)
                if expert_data:
                    return ExpertInstance(**expert_data)
                return None
            else:
                # 回退到纯 Redis 存储
                return await self._get_expert_instance_redis_only(instance_id)
                
        except Exception as e:
            self.logger.error(f"Failed to get expert instance {instance_id}: {str(e)}")
            return None
    
    async def get_team_experts(self, role: Optional[ExpertRole] = None) -> List[ExpertInstance]:
        """Get team expert instances with hybrid storage"""
        
        try:
            if self.hybrid_storage:
                role_value = role.value if role else None
                experts_data = await self.hybrid_storage.get_team_experts(self.team_id, role_value)
                return [ExpertInstance(**expert_data) for expert_data in experts_data]
            else:
                # 回退到纯 Redis 存储
                return await self._get_team_experts_redis_only(role)
                
        except Exception as e:
            self.logger.error(f"Failed to get team experts: {str(e)}")
            return []
    
    # === Redis-only Fallback Methods ===
    
    async def _create_task_redis_only(self, task_data: Dict[str, Any]) -> BlackboardTask:
        """Create task using Redis only (fallback)"""
        task = BlackboardTask(**task_data)
        
        # Store task in Redis
        task_key = f"{self.task_prefix}:{task.task_id}"
        await self._set_redis_value(task_key, task.model_dump_json())
        
        # Update state
        await self._add_task_to_state(task.task_id, TaskStatus.PENDING)
        
        return task
    
    async def _get_task_redis_only(self, task_id: str) -> Optional[BlackboardTask]:
        """Get task using Redis only (fallback)"""
        task_key = f"{self.task_prefix}:{task_id}"
        task_data = await self._get_redis_value(task_key)
        
        if task_data:
            return BlackboardTask.model_validate_json(task_data)
        return None
    
    async def _update_task_status_redis_only(self, task_id: str, status: TaskStatus, **kwargs) -> Optional[BlackboardTask]:
        """Update task status using Redis only (fallback)"""
        task = await self._get_task_redis_only(task_id)
        if task:
            task.status = status
            task.updated_at = datetime.now()
            
            # Update additional fields
            for key, value in kwargs.items():
                if hasattr(task, key):
                    setattr(task, key, value)
            
            # Store updated task
            await self._store_task(task)
            
            # Update state
            old_status = await self._get_task_status_from_redis(task_id)
            if old_status:
                await self._move_task_in_state(task_id, TaskStatus(old_status), status)
            
            return task
        return None
    
    async def _get_tasks_by_status_redis_only(self, status: TaskStatus) -> List[BlackboardTask]:
        """Get tasks by status using Redis only (fallback)"""
        state = await self._get_blackboard_state()
        if not state:
            return []
        
        status_field_map = {
            TaskStatus.PENDING: "pending_tasks",
            TaskStatus.ASSIGNED: "assigned_tasks",
            TaskStatus.IN_PROGRESS: "in_progress_tasks",
            TaskStatus.COMPLETED: "completed_tasks",
            TaskStatus.FAILED: "failed_tasks"
        }
        
        task_ids = getattr(state, status_field_map[status], [])
        tasks = []
        
        for task_id in task_ids:
            task = await self._get_task_redis_only(task_id)
            if task:
                tasks.append(task)
        
        return tasks
    
    async def _create_expert_instance_redis_only(self, expert_data: Dict[str, Any]) -> ExpertInstance:
        """Create expert instance using Redis only (fallback)"""
        expert = ExpertInstance(**expert_data)
        await self._store_expert_instance(expert)
        return expert
    
    async def _get_expert_instance_redis_only(self, instance_id: str) -> Optional[ExpertInstance]:
        """Get expert instance using Redis only (fallback)"""
        expert_key = f"{self.expert_prefix}:{instance_id}"
        expert_data = await self._get_redis_value(expert_key)
        
        if expert_data:
            return ExpertInstance.model_validate_json(expert_data)
        return None
    
    async def _get_team_experts_redis_only(self, role: Optional[ExpertRole] = None) -> List[ExpertInstance]:
        """Get team experts using Redis only (fallback)"""
        pattern = f"{self.expert_prefix}:*"
        expert_keys = await self._get_keys_by_pattern(pattern)
        
        experts = []
        for key in expert_keys:
            expert_data = await self._get_redis_value(key)
            if expert_data:
                expert = ExpertInstance.model_validate_json(expert_data)
                if not role or expert.expert_role == role:
                    experts.append(expert)
        
        return experts
    
    # === Task Query and Search Methods ===
    
    async def get_task(self, task_id: str) -> Optional[BlackboardTask]:
        """Get a specific task by ID"""
        
        try:
            if self.hybrid_storage:
                # 从混合存储获取任务
                task_data = await self.hybrid_storage.get_task(task_id)
                if task_data:
                    return BlackboardTask(**task_data)
                return None
            else:
                # 回退到纯 Redis 存储
                return await self._get_task_redis_only(task_id)
                
        except Exception as e:
            self.logger.error(f"Failed to get task {task_id}: {str(e)}")
            return None
    
    async def search_tasks(self, criteria: TaskSearchCriteria) -> Tuple[List[BlackboardTask], int]:
        """Search tasks based on criteria"""
        
        all_tasks = await self._get_all_tasks() # This method is not hybrid, so it remains Redis-only
        filtered_tasks = []
        
        for task in all_tasks:
            if self._matches_filter(task, criteria.filters):
                if criteria.query:
                    # Simple text search
                    search_text = f"{task.title} {task.description} {task.goal}".lower()
                    if criteria.query.lower() not in search_text:
                        continue
                filtered_tasks.append(task)
        
        # Sort tasks
        if criteria.sort_by == "created_at":
            filtered_tasks.sort(key=lambda x: x.created_at, reverse=(criteria.sort_order == "desc"))
        elif criteria.sort_by == "priority":
            priority_order = {"urgent": 4, "high": 3, "medium": 2, "low": 1}
            filtered_tasks.sort(
                key=lambda x: priority_order.get(x.priority.value, 0),
                reverse=(criteria.sort_order == "desc")
            )
        elif criteria.sort_by == "status":
            filtered_tasks.sort(key=lambda x: x.status.value, reverse=(criteria.sort_order == "desc"))
        
        total_count = len(filtered_tasks)
        
        # Apply pagination
        start = criteria.offset
        end = start + criteria.limit
        paginated_tasks = filtered_tasks[start:end]
        
        return paginated_tasks, total_count
    
    async def get_tasks_by_status(self, status: TaskStatus) -> List[BlackboardTask]:
        """Get all tasks with a specific status using hybrid storage"""
        
        try:
            if self.hybrid_storage:
                # 从混合存储获取任务
                tasks_data = await self.hybrid_storage.get_team_tasks(self.team_id, status.value)
                return [BlackboardTask(**task_data) for task_data in tasks_data]
            else:
                # 回退到纯 Redis 存储
                return await self._get_tasks_by_status_redis_only(status)
                
        except Exception as e:
            self.logger.error(f"Failed to get tasks by status {status}: {str(e)}")
            return []
    
    async def get_tasks_for_expert(self, expert_instance_id: str) -> List[BlackboardTask]:
        """Get all tasks assigned to a specific expert instance"""
        
        all_tasks = await self._get_all_tasks() # This method is not hybrid, so it remains Redis-only
        expert_tasks = []
        
        for task in all_tasks:
            if (task.assignment and 
                task.assignment.expert_instance_id == expert_instance_id):
                expert_tasks.append(task)
        
        return expert_tasks
    
    # === Team and State Management ===
    
    async def get_blackboard_state(self) -> BlackboardState:
        """Get current BlackBoard state"""
        
        state = await self._get_blackboard_state()
        if not state:
            # Create initial state
            state = BlackboardState(team_id=self.team_id)
            await self._store_blackboard_state(state)
        
        # Update statistics
        await self._update_state_statistics(state)
        return state
    
    async def get_team_performance_metrics(self) -> Dict[str, Any]:
        """Get team performance metrics"""
        state = await self.get_blackboard_state()
        
        # Calculate expert utilization
        expert_utilization = {}
        experts = await self.get_team_experts()
        for expert in experts:
            if expert.max_concurrent_tasks > 0:
                utilization = expert.current_task_count / expert.max_concurrent_tasks
                expert_utilization[expert.instance_name] = utilization
        
        return {
            "completion_rate": state.completion_rate,
            "total_tasks": state.total_tasks,
            "pending_tasks": len(state.pending_tasks),
            "in_progress_tasks": len(state.in_progress_tasks),
            "completed_tasks": len(state.completed_tasks),
            "failed_tasks": len(state.failed_tasks),
            "expert_utilization": expert_utilization,
            "last_updated": state.last_updated.isoformat()
        }
    
    # === Notification and Communication ===
    
    async def add_comment(
        self,
        task_id: str,
        author_id: str,
        content: str,
        comment_type: str = "note",
        parent_comment_id: Optional[str] = None
    ) -> CollaborationComment:
        """Add a comment to a task"""
        
        comment = CollaborationComment(
            task_id=task_id,
            author_id=author_id,
            content=content,
            comment_type=comment_type,
            parent_comment_id=parent_comment_id
        )
        
        comment_key = f"{self.comment_prefix}:{task_id}:{comment.comment_id}"
        await self._set_redis_value(comment_key, comment.model_dump_json())
        
        # Notify team members
        await self._notify_team_members(
            task_id,
            "comment_added",
            f"New comment on task",
            f"Comment: {content[:50]}...",
            [author_id]
        )
        
        return comment
    
    async def get_task_comments(self, task_id: str) -> List[CollaborationComment]:
        """Get all comments for a task"""
        
        pattern = f"{self.comment_prefix}:{task_id}:*"
        comment_keys = await self._get_keys_by_pattern(pattern)
        
        comments = []
        for key in comment_keys:
            comment_data = await self._get_redis_value(key)
            if comment_data:
                comment = CollaborationComment.model_validate_json(comment_data)
                comments.append(comment)
        
        # Sort by creation time
        comments.sort(key=lambda x: x.created_at)
        return comments
    
    # === Auto-assignment and Optimization ===
    
    async def auto_assign_task(self, task_id: str) -> bool:
        """Automatically assign a task to the best available expert"""
        
        task = await self.get_task(task_id)
        if not task or task.status != TaskStatus.PENDING:
            return False
        
        # Get available experts
        available_experts = await self.get_available_experts(task.required_expert_role)
        if not available_experts:
            self.logger.warning(f"No available experts for task {task_id}")
            return False
        
        # Select best expert (lowest current load, highest performance)
        best_expert = self._select_best_expert(available_experts, task)
        
        # Assign task
        return await self.assign_task(task_id, best_expert.instance_id, "system")
    
    def _select_best_expert(self, experts: List[ExpertInstance], task: BlackboardTask) -> ExpertInstance:
        """Select the best expert for a task based on load and performance"""
        
        def expert_score(expert: ExpertInstance) -> float:
            # Base score (lower current load is better)
            load_score = 1.0 - (expert.current_task_count / expert.max_concurrent_tasks)
            
            # Performance score
            completed_tasks = expert.performance_metrics.get("completed_tasks", 0)
            failed_tasks = expert.performance_metrics.get("failed_tasks", 0)
            total_tasks = completed_tasks + failed_tasks
            
            if total_tasks > 0:
                success_rate = completed_tasks / total_tasks
            else:
                success_rate = 0.5  # Neutral for new experts
            
            # Specialization bonus
            specialization_bonus = 0.0
            if task.metadata and task.metadata.required_skills:
                matching_skills = set(expert.specializations) & set(task.metadata.required_skills)
                specialization_bonus = len(matching_skills) * 0.1
            
            return load_score * 0.6 + success_rate * 0.3 + specialization_bonus
        
        # Select expert with highest score
        return max(experts, key=expert_score)
    
    # === Helper Methods ===
    
    async def _store_task(self, task: BlackboardTask):
        """Store task in Redis"""
        task_key = f"{self.task_prefix}:{task.task_id}"
        await self._set_redis_value(task_key, task.model_dump_json())
    
    async def _store_expert_instance(self, expert: ExpertInstance):
        """Store expert instance in Redis"""
        expert_key = f"{self.expert_prefix}:{expert.instance_id}"
        await self._set_redis_value(expert_key, expert.model_dump_json())
    
    async def _get_all_tasks(self) -> List[BlackboardTask]:
        """Get all tasks for the team"""
        pattern = f"{self.task_prefix}:*"
        task_keys = await self._get_keys_by_pattern(pattern)
        
        tasks = []
        for key in task_keys:
            task_data = await self._get_redis_value(key)
            if task_data:
                task = BlackboardTask.model_validate_json(task_data)
                tasks.append(task)
        
        return tasks
    
    async def _get_all_expert_instances(self) -> List[ExpertInstance]:
        """Get all expert instances for the team"""
        pattern = f"{self.expert_prefix}:*"
        expert_keys = await self._get_keys_by_pattern(pattern)
        
        experts = []
        for key in expert_keys:
            expert_data = await self._get_redis_value(key)
            if expert_data:
                expert = ExpertInstance.model_validate_json(expert_data)
                experts.append(expert)
        
        return experts
    
    async def get_expert_instance(self, instance_id: str) -> Optional[ExpertInstance]:
        """Get a specific expert instance"""
        expert_key = f"{self.expert_prefix}:{instance_id}"
        expert_data = await self._get_redis_value(expert_key)
        
        if expert_data:
            return ExpertInstance.model_validate_json(expert_data)
        return None
    
    def _matches_filter(self, task: BlackboardTask, filters: TaskFilter) -> bool:
        """Check if task matches filter criteria"""
        
        if filters.status and task.status not in filters.status:
            return False
        
        if filters.priority and task.priority not in filters.priority:
            return False
        
        if filters.expert_role and task.required_expert_role not in filters.expert_role:
            return False
        
        if filters.assigned_to and task.assignment:
            if task.assignment.expert_instance_id not in filters.assigned_to:
                return False
        elif filters.assigned_to:
            return False
        
        if filters.platforms:
            if not any(platform in task.target_platforms for platform in filters.platforms):
                return False
        
        if filters.regions:
            if not any(region in task.target_regions for region in filters.regions):
                return False
        
        if filters.tags and task.metadata:
            if not any(tag in task.metadata.tags for tag in filters.tags):
                return False
        
        if filters.date_range:
            start_date = filters.date_range.get("start")
            end_date = filters.date_range.get("end")
            
            if start_date and task.created_at < start_date:
                return False
            
            if end_date and task.created_at > end_date:
                return False
        
        return True
    
    # === Redis Helper Methods (保持原有功能) ===
    
    async def _set_redis_value(self, key: str, value: str):
        """Store value in Redis with logging"""
        try:
            self.logger.debug(f"Storing Redis key: {key}")
            result = self.redis_client.set(key, value)
            if result:
                self.logger.debug(f"Successfully stored Redis key: {key}")
            else:
                raise Exception(f"Failed to store Redis key: {key}")
        except Exception as e:
            self.logger.error(
                f"Failed to store Redis key {key}: {str(e)}",
                extra={'redis_key': key, 'team_id': self.team_id},
                exc_info=True
            )
            raise
    
    async def _get_redis_value(self, key: str) -> Optional[str]:
        """Get value from Redis with logging"""
        try:
            self.logger.debug(f"Retrieving Redis key: {key}")
            value = self.redis_client.get(key)
            if value is None:
                self.logger.debug(f"Redis key not found: {key}")
            else:
                self.logger.debug(f"Successfully retrieved Redis key: {key}")
            return value
        except Exception as e:
            self.logger.error(
                f"Failed to retrieve Redis key {key}: {str(e)}",
                extra={'redis_key': key, 'team_id': self.team_id},
                exc_info=True
            )
            raise
    
    async def _get_keys_by_pattern(self, pattern: str) -> List[str]:
        """Get keys matching pattern"""
        return self.redis_client.keys(pattern)
    
    async def _get_blackboard_state(self) -> Optional[BlackboardState]:
        """Get BlackBoard state from Redis"""
        state_data = await self._get_redis_value(self.state_key)
        if state_data:
            return BlackboardState.model_validate_json(state_data)
        return None
    
    async def _store_blackboard_state(self, state: BlackboardState):
        """Store BlackBoard state in Redis"""
        await self._set_redis_value(self.state_key, state.model_dump_json())
    
    async def _add_task_to_state(self, task_id: str, status: TaskStatus):
        """Add task to appropriate status list in state"""
        state = await self._get_blackboard_state() or BlackboardState(team_id=self.team_id)
        
        if status == TaskStatus.PENDING:
            state.pending_tasks.append(task_id)
        elif status == TaskStatus.ASSIGNED:
            state.assigned_tasks.append(task_id)
        elif status == TaskStatus.IN_PROGRESS:
            state.in_progress_tasks.append(task_id)
        elif status == TaskStatus.COMPLETED:
            state.completed_tasks.append(task_id)
        elif status == TaskStatus.FAILED:
            state.failed_tasks.append(task_id)
        
        state.total_tasks = len(state.pending_tasks + state.assigned_tasks + 
                                state.in_progress_tasks + state.completed_tasks + 
                                state.failed_tasks)
        state.last_updated = datetime.now()
        
        await self._store_blackboard_state(state)
    
    async def _move_task_in_state(self, task_id: str, from_status: TaskStatus, to_status: TaskStatus):
        """Move task between status lists in state"""
        state = await self._get_blackboard_state()
        if not state:
            return
        
        # Remove from old status
        if from_status == TaskStatus.PENDING and task_id in state.pending_tasks:
            state.pending_tasks.remove(task_id)
        elif from_status == TaskStatus.ASSIGNED and task_id in state.assigned_tasks:
            state.assigned_tasks.remove(task_id)
        elif from_status == TaskStatus.IN_PROGRESS and task_id in state.in_progress_tasks:
            state.in_progress_tasks.remove(task_id)
        
        # Add to new status
        if to_status == TaskStatus.ASSIGNED:
            state.assigned_tasks.append(task_id)
        elif to_status == TaskStatus.IN_PROGRESS:
            state.in_progress_tasks.append(task_id)
        elif to_status == TaskStatus.COMPLETED:
            state.completed_tasks.append(task_id)
        elif to_status == TaskStatus.FAILED:
            state.failed_tasks.append(task_id)
        
        state.last_updated = datetime.now()
        await self._store_blackboard_state(state)
    
    async def _create_event(self, task_id: str, event_type: str, event_data: Dict, triggered_by: str):
        """Create a task event"""
        event = TaskEvent(
            task_id=task_id,
            event_type=event_type,
            event_data=event_data,
            triggered_by=triggered_by
        )
        
        event_key = f"{self.event_prefix}:{task_id}:{event.event_id}"
        await self._set_redis_value(event_key, event.model_dump_json())
    
    async def _notify_team_members(
        self,
        task_id: str,
        notification_type: str,
        title: str,
        message: str,
        exclude_users: List[str] = None
    ):
        """Send notifications to team members"""
        # This would integrate with the actual notification system
        # For now, just log the notification
        self.logger.info(f"Notification: {title} - {message}")
    
    async def _update_state_statistics(self, state: BlackboardState):
        """Update state statistics"""
        total_tasks = len(state.pending_tasks + state.assigned_tasks + 
                         state.in_progress_tasks + state.completed_tasks + 
                         state.failed_tasks)
        
        if total_tasks > 0:
            completed_count = len(state.completed_tasks)
            state.completion_rate = completed_count / total_tasks
        else:
            state.completion_rate = 0.0
        
        state.total_tasks = total_tasks
        state.last_updated = datetime.now()
        
        await self._store_blackboard_state(state)
    
    async def _calculate_expert_utilization(self) -> Dict[str, float]:
        """Calculate utilization rate for each expert instance"""
        experts = await self._get_all_expert_instances()
        utilization = {}
        
        for expert in experts:
            utilization_rate = expert.current_task_count / expert.max_concurrent_tasks
            utilization[expert.instance_id] = utilization_rate
        
        return utilization
    
    async def _calculate_task_distribution(self) -> Dict[str, int]:
        """Calculate task distribution by expert role"""
        all_tasks = await self._get_all_tasks()
        distribution = {role.value: 0 for role in ExpertRole}
        
        for task in all_tasks:
            distribution[task.required_expert_role.value] += 1
        
        return distribution
    
    async def _calculate_performance_trends(self) -> Dict[str, List[float]]:
        """Calculate performance trends over time"""
        # This would calculate trends based on historical data
        # For now, return placeholder data
        return {
            "completion_rate_trend": [0.8, 0.85, 0.9, 0.88, 0.92],
            "average_duration_trend": [45, 42, 40, 38, 35],
            "task_volume_trend": [10, 12, 15, 18, 20]
        } 

    # === Redis Operation Methods with Logging ===
    
    async def _set_redis_value(self, key: str, value: str):
        """Store value in Redis with logging"""
        try:
            self.logger.debug(f"Storing Redis key: {key}")
            result = self.redis_client.set(key, value)
            if result:
                self.logger.debug(f"Successfully stored Redis key: {key}")
            else:
                raise Exception(f"Failed to store Redis key: {key}")
        except Exception as e:
            self.logger.error(
                f"Failed to store Redis key {key}: {str(e)}",
                extra={'redis_key': key, 'team_id': self.team_id},
                exc_info=True
            )
            raise
    
    async def _get_redis_value(self, key: str) -> Optional[str]:
        """Get value from Redis with logging"""
        try:
            self.logger.debug(f"Retrieving Redis key: {key}")
            value = self.redis_client.get(key)
            if value is None:
                self.logger.debug(f"Redis key not found: {key}")
            else:
                self.logger.debug(f"Successfully retrieved Redis key: {key}")
            return value
        except Exception as e:
            self.logger.error(
                f"Failed to retrieve Redis key {key}: {str(e)}",
                extra={'redis_key': key, 'team_id': self.team_id},
                exc_info=True
            )
            raise
    
    async def _delete_redis_key(self, key: str):
        """Delete key from Redis with logging"""
        try:
            self.logger.debug(f"Deleting Redis key: {key}")
            result = self.redis_client.delete(key)
            self.logger.debug(f"Redis key deletion result: {result} for key: {key}")
            return result
        except Exception as e:
            self.logger.error(
                f"Failed to delete Redis key {key}: {str(e)}",
                extra={'redis_key': key, 'team_id': self.team_id},
                exc_info=True
            )
            raise 