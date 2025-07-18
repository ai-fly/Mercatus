import asyncio
import logging
from datetime import datetime
from typing import Dict, List, Optional, Type, Any
from uuid import uuid4

from app.types.blackboard import (
    Team, TeamMember, TeamRole, TeamConfiguration, ExpertInstance, ExpertRole,
    BlackboardTask, TaskStatus, TaskPriority, TaskSearchCriteria, TaskFilter,
    Platform, Region, ContentType
)
from app.core.blackboard import BlackBoard
from app.experts.expert import ExpertBase
from app.experts.plan_expert import PlanExpert
from app.experts.content_expert import ContentExpert
from app.experts.rewiew_expert import ReviewExpert
from app.clients.redis_client import redis_client_instance
from app.config import settings
from app.utils.logging import get_business_logger, get_performance_logger
from app.core.continuous_monitor import ContinuousMonitoringService


class TeamManager:
    """
    Multi-tenant team management system that coordinates BlackBoard instances,
    expert instances, and team collaboration for the Mercatus content factory.
    Now uses hybrid storage: PostgreSQL for persistence + Redis for caching.
    """
    
    def __init__(self, hybrid_storage_service=None):
        """Initialize TeamManager"""
        self.redis_client = redis_client_instance.get_redis_client()
        self.logger = logging.getLogger("TeamManager")
        self.business_logger = get_business_logger()
        self.performance_logger = get_performance_logger()
        
        # 混合存储服务
        self.hybrid_storage = hybrid_storage_service
        
        self.teams: Dict[str, Team] = {}
        self.blackboards: Dict[str, BlackBoard] = {}
        self.expert_instances: Dict[str, Dict[str, ExpertBase]] = {}  # team_id -> instance_id -> expert
        self.monitoring_services: Dict[str, 'ContinuousMonitoringService'] = {}  # team_id -> monitoring service
        
        # Expert class mapping
        self.expert_classes = {
            ExpertRole.PLANNER: PlanExpert,
            ExpertRole.EXECUTOR: ContentExpert,
            ExpertRole.EVALUATOR: ReviewExpert
        }
        
        self.logger.info("TeamManager initialized with hybrid storage")
    
    # === Team Management (Hybrid Storage) ===
    
    async def create_team(
        self,
        team_name: str,
        organization_id: str,
        owner_id: str,
        owner_username: str
    ) -> Team:
        """Create a new team with hybrid storage"""
        
        with self.performance_logger.time_operation(
            "team_manager_create_team",
            organization_id=organization_id,
            owner_id=owner_id
        ):
            try:
                # 准备团队数据
                team_data = {
                    "team_id": str(uuid4()),
                    "team_name": team_name,
                    "organization_id": organization_id,
                    "owner_id": owner_id,
                    "is_active": True,
                    "max_jeff_instances": 1,
                    "max_monica_instances": 3,
                    "max_henry_instances": 2,
                    "auto_scaling_enabled": True,
                    "jeff_scaling_enabled": False,
                    "task_queue_limit": 100,
                    "concurrent_task_limit": 10,
                    "total_tasks_completed": 0,
                    "total_content_generated": 0,
                    "team_performance_score": 0.0
                }
                
                # 使用混合存储创建团队
                if self.hybrid_storage:
                    result = await self.hybrid_storage.create_team(team_data)
                    if result["status"] == "success":
                        team = Team(**result["team"])
                        
                        # 创建 BlackBoard 实例
                        blackboard = BlackBoard(team.team_id, self.hybrid_storage)
                        self.blackboards[team.team_id] = blackboard
                        
                        # 初始化专家实例
                        await self._initialize_expert_instances(team.team_id)
                        
                        # 启动监控服务
                        await self._start_monitoring_service(team.team_id)
                        
                        self.logger.info(
                            f"Team created successfully with hybrid storage: {team.team_id}",
                            extra={
                                'team_id': team.team_id,
                                'team_name': team_name,
                                'organization_id': organization_id,
                                'owner_id': owner_id,
                                'storage_type': 'hybrid'
                            }
                        )
                        
                        return team
                    else:
                        raise Exception(f"Failed to create team: {result['message']}")
                else:
                    # 回退到纯 Redis 存储
                    return await self._create_team_redis_only(team_data)
                    
            except Exception as e:
                self.logger.error(f"Failed to create team: {str(e)}")
                raise
    
    async def add_team_member(
        self,
        team_id: str,
        user_id: str,
        username: str,
        role: TeamRole,
        added_by: str
    ) -> bool:
        """Add a member to a team"""
        
        with self.performance_logger.time_operation(
            "add_team_member",
            team_id=team_id,
            target_user_id=user_id,
            role=role.value
        ):
            team = await self.get_team(team_id)
            if not team:
                self.logger.error(
                    f"Cannot add member to team {team_id}: team not found",
                    extra={'team_id': team_id, 'user_id': added_by, 'target_user_id': user_id}
                )
                return False
            
            # Check if user is already a member
            if any(member.user_id == user_id for member in team.members):
                self.logger.warning(
                    f"User {user_id} already member of team {team_id}",
                    extra={
                        'team_id': team_id,
                        'user_id': added_by,
                        'target_user_id': user_id,
                        'action': 'add_member_duplicate'
                    }
                )
                return False
            
            # Add member
            member = TeamMember(
                user_id=user_id,
                username=username,
                role=role
            )
            team.members.append(member)
            team.updated_at = datetime.now()
            
            await self._store_team(team)
            
            self.logger.info(
                f"Added member {user_id} to team {team_id}",
                extra={
                    'team_id': team_id,
                    'user_id': added_by,
                    'target_user_id': user_id,
                    'target_username': username,
                    'role': role.value,
                    'total_members': len(team.members),
                    'action': 'member_added'
                }
            )
            
            return True
    
    async def remove_team_member(self, team_id: str, user_id: str, removed_by: str) -> bool:
        """Remove a member from a team"""
        
        team = await self.get_team(team_id)
        if not team:
            return False
        
        # Cannot remove owner
        if user_id == team.owner_id:
            self.logger.error(f"Cannot remove team owner {user_id} from team {team_id}")
            return False
        
        # Find and remove member
        for i, member in enumerate(team.members):
            if member.user_id == user_id:
                team.members.pop(i)
                team.updated_at = datetime.now()
                
                await self._store_team(team)
                self.teams[team_id] = team
                
                self.logger.info(f"Removed member {user_id} from team {team_id}")
                return True
        
        return False
    
    async def get_team(self, team_id: str) -> Optional[Team]:
        """Get team by ID with hybrid storage"""
        
        try:
            if self.hybrid_storage:
                team_data = await self.hybrid_storage.get_team(team_id)
                if team_data:
                    return Team(**team_data)
                return None
            else:
                # 回退到纯 Redis 存储
                return await self._get_team_redis_only(team_id)
                
        except Exception as e:
            self.logger.error(f"Failed to get team {team_id}: {str(e)}")
            return None
    
    async def get_user_teams(self, user_id: str) -> List[Team]:
        """Get all teams for a user with hybrid storage"""
        
        try:
            if self.hybrid_storage:
                teams_data = await self.hybrid_storage.get_user_teams(user_id)
                return [Team(**team_data) for team_data in teams_data]
            else:
                # 回退到纯 Redis 存储
                return await self._get_user_teams_redis_only(user_id)
                
        except Exception as e:
            self.logger.error(f"Failed to get user teams: {str(e)}")
            return []
    
    # === Expert Instance Management ===
    
    async def create_expert_instance(
        self,
        team_id: str,
        expert_role: ExpertRole,
        instance_name: Optional[str] = None,
        max_concurrent_tasks: int = 3,
        specializations: List[str] = None,
        is_team_leader: bool = False
    ) -> Optional[ExpertInstance]:
        """Create a new expert instance with hybrid storage"""
        
        try:
            # 准备专家数据
            expert_data = {
                "instance_id": str(uuid4()),
                "team_id": team_id,
                "expert_role": expert_role.value,
                "instance_name": instance_name or f"{expert_role.value.title()} {len(self._get_team_experts(team_id, expert_role)) + 1}",
                "status": "active",
                "max_concurrent_tasks": max_concurrent_tasks,
                "current_task_count": 0,
                "specializations": specializations or [],
                "performance_metrics": {},
                "is_team_leader": is_team_leader
            }
            
            # 使用混合存储创建专家实例
            if self.hybrid_storage:
                result = await self.hybrid_storage.create_expert_instance(expert_data)
                if result["status"] == "success":
                    expert = ExpertInstance(**result["expert"])
                    
                    # 创建专家实例对象
                    expert_class = self.expert_classes[expert_role]
                    expert_instance = expert_class(index=len(self._get_team_experts(team_id, expert_role)) + 1)
                    
                    # 存储专家实例
                    if team_id not in self.expert_instances:
                        self.expert_instances[team_id] = {}
                    self.expert_instances[team_id][expert.instance_id] = expert_instance
                    
                    self.logger.info(
                        f"Expert instance created successfully: {expert.instance_id}",
                        extra={
                            'team_id': team_id,
                            'expert_role': expert_role.value,
                            'instance_name': expert.instance_name,
                            'storage_type': 'hybrid'
                        }
                    )
                    
                    return expert
                else:
                    raise Exception(f"Failed to create expert instance: {result['message']}")
            else:
                # 回退到纯 Redis 存储
                return await self._create_expert_instance_redis_only(expert_data)
                
        except Exception as e:
            self.logger.error(f"Failed to create expert instance: {str(e)}")
            raise
    
    async def scale_experts(self, team_id: str, expert_role: ExpertRole, target_count: int) -> bool:
        """Scale expert instances for a role to target count"""
        
        team = await self.get_team(team_id)
        if not team:
            return False
        
        current_instances = [e for e in team.expert_instances if e.expert_role == expert_role]
        current_count = len(current_instances)
        
        if target_count == current_count:
            return True
        
        if target_count > current_count:
            # Scale up
            for i in range(target_count - current_count):
                await self.create_expert_instance(team_id, expert_role)
        else:
            # Scale down
            instances_to_remove = current_instances[target_count:]
            for instance in instances_to_remove:
                await self.remove_expert_instance(team_id, instance.instance_id)
        
        return True
    
    async def remove_expert_instance(self, team_id: str, instance_id: str) -> bool:
        """Remove an expert instance"""
        
        team = await self.get_team(team_id)
        if not team:
            return False
        
        # Find and remove instance
        for i, instance in enumerate(team.expert_instances):
            if instance.instance_id == instance_id:
                # Check if instance has active tasks
                blackboard = self.get_blackboard(team_id)
                if blackboard:
                    active_tasks = await blackboard.get_tasks_for_expert(instance_id)
                    if active_tasks:
                        self.logger.warning(f"Cannot remove expert {instance_id} with active tasks")
                        return False
                
                # Remove from team
                team.expert_instances.pop(i)
                team.updated_at = datetime.now()
                await self._store_team(team)
                
                # Remove from memory
                if team_id in self.expert_instances and instance_id in self.expert_instances[team_id]:
                    del self.expert_instances[team_id][instance_id]
                
                self.logger.info(f"Removed expert instance {instance_id}")
                return True
        
        return False
    
    async def get_expert_instance(self, team_id: str, instance_id: str) -> Optional[ExpertBase]:
        """Get expert instance object"""
        
        if team_id in self.expert_instances and instance_id in self.expert_instances[team_id]:
            return self.expert_instances[team_id][instance_id]
        
        return None
    
    # === Task Management Interface ===
    
    def get_blackboard(self, team_id: str) -> Optional[BlackBoard]:
        """Get BlackBoard instance for a team"""
        
        if team_id in self.blackboards:
            return self.blackboards[team_id]
        
        # Create if team exists
        if team_id in self.teams:
            blackboard = BlackBoard(team_id, self.hybrid_storage)
            self.blackboards[team_id] = blackboard
            return blackboard
        
        return None
    
    async def submit_task(
        self,
        team_id: str,
        title: str,
        description: str,
        goal: str,
        required_expert_role: ExpertRole,
        creator_id: str,
        **kwargs
    ) -> Optional[BlackboardTask]:
        """Submit a task to team's BlackBoard"""
        
        blackboard = self.get_blackboard(team_id)
        if not blackboard:
            return None
        
        task = await blackboard.create_task(
            title=title,
            description=description,
            goal=goal,
            required_expert_role=required_expert_role,
            creator_id=creator_id,
            **kwargs
        )
        
        # Attempt auto-assignment
        await blackboard.auto_assign_task(task.task_id)
        
        return task
    
    async def execute_task(self, team_id: str, task_id: str) -> Dict[str, Any]:
        """Execute a task using assigned expert instance with hybrid storage"""
        
        with self.performance_logger.time_operation(
            "execute_task",
            team_id=team_id,
            task_id=task_id
        ):
            self.logger.info(
                f"Starting task execution for task {task_id}",
                extra={
                    'team_id': team_id,
                    'task_id': task_id,
                    'action': 'task_execution_request'
                }
            )
            
            blackboard = self.get_blackboard(team_id)
            if not blackboard:
                self.logger.error(
                    f"Team {team_id} not found for task execution",
                    extra={'team_id': team_id, 'task_id': task_id}
                )
                return {"status": "error", "message": "Team not found"}
            
            task = await blackboard.get_task(task_id)
            if not task or not task.assignment:
                self.logger.error(
                    f"Task {task_id} not found or not assigned",
                    extra={
                        'team_id': team_id,
                        'task_id': task_id,
                        'task_exists': task is not None,
                        'task_assigned': task.assignment is not None if task else False
                    }
                )
                return {"status": "error", "message": "Task not found or not assigned"}
            
            # Get expert instance
            expert = await self.get_expert_instance(team_id, task.assignment.expert_instance_id)
            if not expert:
                self.logger.error(
                    f"Expert instance {task.assignment.expert_instance_id} not found",
                    extra={
                        'team_id': team_id,
                        'task_id': task_id,
                        'expert_instance_id': task.assignment.expert_instance_id
                    }
                )
                return {"status": "error", "message": "Expert instance not found"}
            
            # Log expert details
            expert_type = task.required_expert_role.value
            self.logger.info(
                f"Executing task {task_id} with {expert_type} expert",
                extra={
                    'team_id': team_id,
                    'task_id': task_id,
                    'expert_type': expert_type,
                    'expert_instance_id': task.assignment.expert_instance_id,
                    'task_title': task.title,
                    'task_priority': task.priority.value,
                    'action': 'expert_execution_start'
                }
            )
            
            # Start task
            await blackboard.start_task(task_id, task.assignment.expert_instance_id)
            
            start_time = datetime.now()
            
            try:
                # Execute task
                from app.experts.expert import ExpertTask
                expert_task = ExpertTask(
                    task_name=task.title,
                    task_description=task.description,
                    task_goal=task.goal
                )
                
                self.logger.debug(
                    f"Calling expert.run() for task {task_id}",
                    extra={
                        'team_id': team_id,
                        'task_id': task_id,
                        'expert_type': expert_type,
                        'task_name': task.title
                    }
                )
                
                result = await expert.run(expert_task)
                
                execution_time = (datetime.now() - start_time).total_seconds()
                
                # Complete task
                await blackboard.complete_task(
                    task_id,
                    task.assignment.expert_instance_id,
                    output_data=result,
                    execution_log=[f"Task executed by {expert.name}"]
                )
                
                self.logger.info(
                    f"Task {task_id} completed successfully",
                    extra={
                        'team_id': team_id,
                        'task_id': task_id,
                        'expert_type': expert_type,
                        'execution_time': execution_time,
                        'result_status': result.get('status', 'unknown') if isinstance(result, dict) else 'unknown',
                        'action': 'task_execution_success'
                    }
                )
                
                return {"status": "completed", "result": result}
                
            except Exception as e:
                execution_time = (datetime.now() - start_time).total_seconds()
                
                self.logger.error(
                    f"Task {task_id} execution failed: {str(e)}",
                    extra={
                        'team_id': team_id,
                        'task_id': task_id,
                        'expert_type': expert_type,
                        'execution_time': execution_time,
                        'error_type': type(e).__name__,
                        'action': 'task_execution_failed'
                    },
                    exc_info=True
                )
                
                # Fail task
                await blackboard.fail_task(
                    task_id,
                    task.assignment.expert_instance_id,
                    error_messages=[str(e)]
                )
                
                return {"status": "failed", "error": str(e)}
    
    # === Team Dashboard and Analytics ===
    
    async def get_team_dashboard(self, team_id: str) -> Dict[str, Any]:
        """Get comprehensive team dashboard data"""
        
        team = await self.get_team(team_id)
        blackboard = self.get_blackboard(team_id)
        
        if not team or not blackboard:
            return {}
        
        # Get BlackBoard state
        state = await blackboard.get_blackboard_state()
        
        # Get performance metrics
        performance = await blackboard.get_team_performance_metrics()
        
        # Get recent tasks
        recent_tasks_criteria = TaskSearchCriteria(
            sort_by="created_at",
            sort_order="desc",
            limit=10
        )
        recent_tasks, _ = await blackboard.search_tasks(recent_tasks_criteria)
        
        # Get expert status
        expert_status = []
        for instance in team.expert_instances:
            expert_obj = await self.get_expert_instance(team_id, instance.instance_id)
            active_tasks = await blackboard.get_tasks_for_expert(instance.instance_id)
            
            expert_status.append({
                "instance_id": instance.instance_id,
                "name": instance.instance_name,
                "role": instance.expert_role.value,
                "status": instance.status,
                "current_tasks": len(active_tasks),
                "max_tasks": instance.max_concurrent_tasks,
                "utilization": len(active_tasks) / instance.max_concurrent_tasks,
                "performance": instance.performance_metrics
            })
        
        return {
            "team": team.model_dump(),
            "state": state.model_dump(),
            "performance": performance,
            "recent_tasks": [t.model_dump() for t in recent_tasks],
            "expert_status": expert_status,
            "team_metrics": {
                "total_members": len(team.members),
                "total_experts": len(team.expert_instances),
                "active_experts": len([e for e in team.expert_instances if e.status == "active"]),
                "total_tasks_completed": team.total_tasks_completed,
                "total_content_generated": team.total_content_generated,
                "team_performance_score": team.team_performance_score
            }
        }
    
    async def get_organization_overview(self, organization_id: str) -> Dict[str, Any]:
        """Get overview of all teams in an organization"""
        
        all_teams = await self._get_all_teams()
        org_teams = [team for team in all_teams if team.organization_id == organization_id]
        
        total_members = sum(len(team.members) for team in org_teams)
        total_experts = sum(len(team.expert_instances) for team in org_teams)
        total_tasks = sum(team.total_tasks_completed for team in org_teams)
        total_content = sum(team.total_content_generated for team in org_teams)
        
        active_teams = len([team for team in org_teams if team.is_active])
        
        return {
            "organization_id": organization_id,
            "total_teams": len(org_teams),
            "active_teams": active_teams,
            "total_members": total_members,
            "total_experts": total_experts,
            "total_tasks_completed": total_tasks,
            "total_content_generated": total_content,
            "teams": [
                {
                    "team_id": team.team_id,
                    "team_name": team.team_name,
                    "members": len(team.members),
                    "experts": len(team.expert_instances),
                    "performance_score": team.team_performance_score,
                    "is_active": team.is_active
                }
                for team in org_teams
            ]
        }
    
    # === Auto-scaling and Optimization ===
    
    async def auto_scale_team(self, team_id: str) -> Dict[str, Any]:
        """Automatically scale team experts based on workload"""
        
        team = await self.get_team(team_id)
        blackboard = self.get_blackboard(team_id)
        
        if not team or not blackboard or not team.configuration.auto_scaling_enabled:
            return {"status": "disabled", "message": "Auto-scaling not enabled"}
        
        scaling_actions = []
        
        # Analyze workload for each expert role
        for role in ExpertRole:
            # Special handling for Jeff (team leader) - never scale
            if role == ExpertRole.PLANNER:
                # Jeff is the unique team leader - ensure exactly one instance exists
                current_instances = [e for e in team.expert_instances if e.expert_role == role]
                current_count = len(current_instances)
                
                if current_count == 0:
                    # Emergency: create Jeff if missing
                    jeff_instance = await self.create_expert_instance(
                        team_id, 
                        ExpertRole.PLANNER,
                        "Jeff - Team Leader",
                        max_concurrent_tasks=5,
                        specializations=["strategy_planning", "team_leadership", "market_analysis", "budget_planning"]
                    )
                    if jeff_instance:
                        jeff_instance.is_team_leader = True
                        scaling_actions.append("Emergency: Created missing team leader Jeff")
                elif current_count > 1:
                    # Emergency: remove excess Jeff instances (should never happen)
                    for i in range(1, current_count):
                        if await self.remove_expert_instance(team_id, current_instances[i].instance_id):
                            scaling_actions.append(f"Emergency: Removed excess leader instance {current_instances[i].instance_name}")
                
                # Skip normal scaling logic for Jeff
                continue
            
            # Normal scaling logic for Monica and Henry
            # Get pending tasks for this role
            pending_filter = TaskFilter(
                status=[TaskStatus.PENDING],
                expert_role=[role]
            )
            pending_criteria = TaskSearchCriteria(filters=pending_filter)
            pending_tasks, pending_count = await blackboard.search_tasks(pending_criteria)
            
            # Get current instances
            current_instances = [e for e in team.expert_instances if e.expert_role == role]
            current_count = len(current_instances)
            
            # Calculate required instances based on pending workload
            max_allowed = self._get_max_instances_for_role(team.configuration, role)
            avg_tasks_per_instance = 3  # Configurable
            required_count = min(max_allowed, max(1, (pending_count + avg_tasks_per_instance - 1) // avg_tasks_per_instance))
            
            if required_count > current_count:
                # Scale up
                instances_to_add = required_count - current_count
                for _ in range(instances_to_add):
                    instance = await self.create_expert_instance(team_id, role)
                    if instance:
                        scaling_actions.append(f"Added {role.value} instance: {instance.instance_name}")
            
            elif required_count < current_count and pending_count == 0:
                # Scale down (only if no pending tasks)
                instances_to_remove = current_count - required_count
                removable_instances = [i for i in current_instances if i.current_task_count == 0]
                
                for i in range(min(instances_to_remove, len(removable_instances))):
                    if await self.remove_expert_instance(team_id, removable_instances[i].instance_id):
                        scaling_actions.append(f"Removed {role.value} instance: {removable_instances[i].instance_name}")
        
        return {
            "status": "completed",
            "actions": scaling_actions,
            "timestamp": datetime.now()
        }
    
    # === Monitoring Service Management ===
    
    def get_monitoring_service(self, team_id: str) -> Optional['ContinuousMonitoringService']:
        """Get monitoring service for a team"""
        return self.monitoring_services.get(team_id)
    
    async def stop_team_monitoring(self, team_id: str) -> bool:
        """Stop monitoring service for a team"""
        
        monitoring_service = self.monitoring_services.get(team_id)
        if not monitoring_service:
            return False
        
        try:
            await monitoring_service.stop_monitoring()
            del self.monitoring_services[team_id]
            
            self.logger.info(
                f"Stopped monitoring service for team {team_id}",
                extra={
                    'team_id': team_id,
                    'action': 'monitoring_stopped'
                }
            )
            
            return True
            
        except Exception as e:
            self.logger.error(
                f"Error stopping monitoring for team {team_id}: {str(e)}",
                extra={'team_id': team_id, 'error': str(e)},
                exc_info=True
            )
            return False
    
    async def get_team_workflow_status(self, team_id: str) -> Dict:
        """Get comprehensive workflow status for a team"""
        
        monitoring_service = self.monitoring_services.get(team_id)
        if not monitoring_service:
            return {
                "status": "no_monitoring",
                "message": "Monitoring service not found for this team"
            }
        
        try:
            # Get monitoring dashboard
            dashboard = await monitoring_service.get_monitoring_dashboard()
            
            # Get active workflows
            workflows = await monitoring_service.workflow_engine.list_workflows()
            
            # Get dependency status
            dependency_status = await monitoring_service.dependency_manager.get_dependency_status()
            
            return {
                "status": "active",
                "team_id": team_id,
                "monitoring_dashboard": dashboard,
                "workflows": workflows,
                "dependency_status": dependency_status,
                "last_update": datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(
                f"Error getting workflow status for team {team_id}: {str(e)}",
                extra={'team_id': team_id, 'error': str(e)},
                exc_info=True
            )
            return {
                "status": "error",
                "message": str(e)
            }
    
    async def create_auto_marketing_workflow(
        self,
        team_id: str,
        project_name: str,
        project_description: str,
        target_platforms: List = None,
        target_regions: List = None,
        content_types: List = None,
        creator_id: str = "system"
    ) -> Dict:
        """Create and start an automated marketing workflow"""
        
        monitoring_service = self.monitoring_services.get(team_id)
        if not monitoring_service:
            return {
                "status": "error",
                "message": "Monitoring service not found for this team"
            }
        
        try:
            # Create workflow through the workflow engine
            workflow = await monitoring_service.workflow_engine.create_marketing_workflow(
                project_name=project_name,
                project_description=project_description,
                target_platforms=target_platforms or [],
                target_regions=target_regions or [],
                content_types=content_types or [],
                creator_id=creator_id
            )
            
            # Start the workflow
            workflow_started = await monitoring_service.workflow_engine.start_workflow(workflow.workflow_id)
            
            if workflow_started:
                self.logger.info(
                    f"Auto marketing workflow created and started for team {team_id}",
                    extra={
                        'team_id': team_id,
                        'workflow_id': workflow.workflow_id,
                        'project_name': project_name,
                        'node_count': len(workflow.nodes),
                        'action': 'auto_marketing_workflow_created'
                    }
                )
                
                return {
                    "status": "success",
                    "workflow_id": workflow.workflow_id,
                    "workflow_name": workflow.workflow_name,
                    "nodes": len(workflow.nodes),
                    "message": f"Marketing workflow '{project_name}' created and started successfully"
                }
            else:
                return {
                    "status": "error",
                    "message": "Failed to start workflow"
                }
            
        except Exception as e:
            self.logger.error(
                f"Error creating auto marketing workflow for team {team_id}: {str(e)}",
                extra={
                    'team_id': team_id,
                    'project_name': project_name,
                    'error': str(e)
                },
                exc_info=True
            )
            return {
                "status": "error",
                "message": str(e)
            }
    
    # === Helper Methods ===
    
    async def _initialize_team_experts(self, team: Team):
        """Initialize default expert instances for a new team"""
        
        # Create single Jeff instance (team leader)
        jeff_instance = await self.create_expert_instance(
            team.team_id,
            ExpertRole.PLANNER,
            "Jeff - Team Leader",
            max_concurrent_tasks=5,  # Leader handles more tasks
            specializations=["strategy_planning", "team_leadership", "market_analysis", "budget_planning"]
        )
        if jeff_instance:
            # Mark Jeff as team leader
            jeff_instance.is_team_leader = True
            # Update the team data to reflect leader status
            for i, expert in enumerate(team.expert_instances):
                if expert.instance_id == jeff_instance.instance_id:
                    team.expert_instances[i].is_team_leader = True
                    break
            await self._store_team(team)
        
        # Create initial Monica instances (executors)
        for i in range(2):  # Start with 2 Monicas
            await self.create_expert_instance(
                team.team_id,
                ExpertRole.EXECUTOR,
                f"Monica {i+1}",
                max_concurrent_tasks=3
            )
        
        # Create initial Henry instances (evaluators)
        for i in range(1):  # Start with 1 Henry
            await self.create_expert_instance(
                team.team_id,
                ExpertRole.EVALUATOR,
                f"Henry {i+1}",
                max_concurrent_tasks=3
            )
    
    async def _start_auto_workflow_system(self, team: Team):
        """Start automatic workflow system for a new team"""
        
        try:
            # Import here to avoid circular imports
            from app.core.continuous_monitor import ContinuousMonitoringService
            from app.core.workflow_engine import WorkflowEngine
            
            self.logger.info(
                f"Starting auto workflow system for team {team.team_id}",
                extra={
                    'team_id': team.team_id,
                    'team_name': team.team_name,
                    'action': 'auto_workflow_system_start'
                }
            )
            
            # Create and start monitoring service
            monitoring_service = ContinuousMonitoringService(team.team_id)
            self.monitoring_services[team.team_id] = monitoring_service
            
            # Start monitoring service
            await monitoring_service.start_monitoring()
            
            # Trigger team kick-off planning
            await self._trigger_team_kickoff_planning(team.team_id, team.owner_id)
            
            # Create a welcome/demo workflow to showcase the system
            await self._create_demo_workflow(team.team_id, team.owner_id)
            
            self.logger.info(
                f"Auto workflow system started for team {team.team_id}",
                extra={
                    'team_id': team.team_id,
                    'monitoring_started': True,
                    'kickoff_planning_triggered': True,
                    'demo_workflow_created': True,
                    'action': 'auto_workflow_system_started'
                }
            )
            
        except Exception as e:
            self.logger.error(
                f"Error starting auto workflow system for team {team.team_id}: {str(e)}",
                extra={
                    'team_id': team.team_id,
                    'error': str(e),
                    'action': 'auto_workflow_system_error'
                },
                exc_info=True
            )
    
    async def _trigger_team_kickoff_planning(self, team_id: str, creator_id: str):
        """Trigger the team kick-off planning workflow."""
        monitoring_service = self.monitoring_services.get(team_id)
        if not monitoring_service:
            self.logger.warning(
                f"Cannot trigger kick-off planning for team {team_id}: monitoring service not found.",
                extra={'team_id': team_id}
            )
            return

        try:
            # Create a new task for kick-off planning
            blackboard = self.get_blackboard(team_id)
            if not blackboard:
                self.logger.error(
                    f"Cannot create kick-off planning task for team {team_id}: BlackBoard not found.",
                    extra={'team_id': team_id}
                )
                return

            task_title = "团队启动规划"
            task_description = "请团队成员讨论并制定团队启动计划，包括目标、策略和资源分配。"
            task_goal = "制定团队启动计划"
            required_expert_role = ExpertRole.PLANNER # Assuming the planner is the one who initiates

            task = await blackboard.create_task(
                title=task_title,
                description=task_description,
                goal=task_goal,
                required_expert_role=required_expert_role,
                creator_id=creator_id
            )

            await blackboard.auto_assign_task(task.task_id)
            self.logger.info(
                f"Kick-off planning task created for team {team_id}",
                extra={
                    'team_id': team_id,
                    'task_id': task.task_id,
                    'task_title': task.title,
                    'action': 'kickoff_planning_task_created'
                }
            )

            # Start the workflow for the new task
            workflow_engine = monitoring_service.workflow_engine
            workflow = await workflow_engine.create_workflow(
                workflow_name=f"团队启动规划流程_{task.task_id}",
                workflow_description=f"为团队 {task.title} 制定执行计划",
                nodes=[
                    {
                        "node_type": "task_assignment",
                        "task_id": task.task_id,
                        "expert_role": required_expert_role.value,
                        "max_retries": 3,
                        "retry_delay": 300,
                        "timeout": 3600
                    }
                ],
                creator_id=creator_id
            )
            await workflow_engine.start_workflow(workflow.workflow_id)
            self.logger.info(
                f"Kick-off planning workflow started for team {team_id}",
                extra={
                    'team_id': team_id,
                    'workflow_id': workflow.workflow_id,
                    'workflow_name': workflow.workflow_name,
                    'node_count': len(workflow.nodes),
                    'action': 'kickoff_planning_workflow_started'
                }
            )

        except Exception as e:
            self.logger.error(
                f"Error triggering kick-off planning for team {team_id}: {str(e)}",
                extra={
                    'team_id': team_id,
                    'error': str(e),
                    'action': 'kickoff_planning_error'
                },
                exc_info=True
            )
    
    async def _create_demo_workflow(self, team_id: str, creator_id: str):
        """Create a demo workflow to showcase the system capabilities"""
        
        try:
            monitoring_service = self.monitoring_services.get(team_id)
            if not monitoring_service:
                return
            
            # Create a simple demo marketing workflow
            workflow = await monitoring_service.workflow_engine.create_marketing_workflow(
                project_name="团队能力展示",
                project_description="展示Mercatus多智能体系统的营销策略制定、内容生成和合规审核能力",
                target_platforms=["twitter", "facebook"], 
                target_regions=["us", "cn"],
                content_types=["text", "text_image"],
                creator_id=creator_id
            )
            
            # Start the workflow
            await monitoring_service.workflow_engine.start_workflow(workflow.workflow_id)
            
            self.logger.info(
                f"Demo workflow created and started for team {team_id}",
                extra={
                    'team_id': team_id,
                    'workflow_id': workflow.workflow_id,
                    'workflow_name': workflow.workflow_name,
                    'node_count': len(workflow.nodes),
                    'action': 'demo_workflow_created'
                }
            )
            
        except Exception as e:
            self.logger.error(
                f"Error creating demo workflow for team {team_id}: {str(e)}",
                extra={'team_id': team_id, 'error': str(e)},
                exc_info=True
            )
    
    async def handle_task_max_retries_reached(self, team_id: str, task_id: str, failed_by: str = "system") -> bool:
        """Handle when a task reaches maximum retries and trigger Jeff's replanning"""
        
        try:
            blackboard = self.get_blackboard(team_id)
            if not blackboard:
                self.logger.error(f"BlackBoard not found for team {team_id}")
                return False
            
            # Get the failed task
            failed_task = await blackboard.get_task(task_id)
            if not failed_task:
                self.logger.error(f"Task {task_id} not found")
                return False
            
            # Mark task as requiring replanning
            failed_task.requires_replanning = True
            failed_task.last_failure_timestamp = datetime.now()
            await blackboard._store_task(failed_task)
            
            self.logger.warning(
                f"Task {task_id} reached max retries, triggering replanning",
                extra={
                    'team_id': team_id,
                    'task_id': task_id,
                    'retry_count': failed_task.retry_count,
                    'max_retries': failed_task.max_retries,
                    'action': 'max_retries_reached'
                }
            )
            
            # Trigger Jeff's replanning for all incomplete tasks
            await self._trigger_failure_replanning(team_id, task_id, failed_by)
            
            return True
            
        except Exception as e:
            self.logger.error(
                f"Error handling max retries for task {task_id}: {str(e)}",
                extra={
                    'team_id': team_id,
                    'task_id': task_id,
                    'error': str(e),
                    'action': 'max_retries_handling_error'
                },
                exc_info=True
            )
            return False
    
    async def _trigger_failure_replanning(self, team_id: str, failed_task_id: str, creator_id: str):
        """Trigger Jeff's replanning due to task failure"""
        
        try:
            blackboard = self.get_blackboard(team_id)
            if not blackboard:
                return
            
            # Get all incomplete tasks for replanning
            from app.types.blackboard import TaskFilter, TaskSearchCriteria, TaskStatus
            
            incomplete_filter = TaskFilter(
                status=[TaskStatus.PENDING, TaskStatus.ASSIGNED, TaskStatus.IN_PROGRESS, TaskStatus.FAILED]
            )
            incomplete_criteria = TaskSearchCriteria(filters=incomplete_filter)
            incomplete_tasks, _ = await blackboard.search_tasks(incomplete_criteria)
            
            # Create replanning task for Jeff
            replanning_task = await blackboard.create_task(
                title=f"任务失败重新规划 - 基于失败任务 {failed_task_id}",
                description=f"由于任务 {failed_task_id} 达到最大重试次数失败，需要对当前所有未完成任务进行重新规划和策略调整",
                goal="重新评估和规划所有未完成任务，制定新的执行策略",
                required_expert_role=ExpertRole.PLANNER,
                creator_id=creator_id,
                metadata={
                    "context_data": {
                        "trigger_type": "task_failure_replan",
                        "failed_task_id": failed_task_id,
                        "incomplete_task_count": len(incomplete_tasks),
                        "incomplete_task_ids": [task.task_id for task in incomplete_tasks]
                    }
                }
            )
            
            # Auto-assign to Jeff (team leader)
            await blackboard.auto_assign_task(replanning_task.task_id)
            
            self.logger.info(
                f"Failure replanning task created for team {team_id}",
                extra={
                    'team_id': team_id,
                    'replanning_task_id': replanning_task.task_id,
                    'failed_task_id': failed_task_id,
                    'incomplete_task_count': len(incomplete_tasks),
                    'action': 'failure_replanning_triggered'
                }
            )
            
        except Exception as e:
            self.logger.error(
                f"Error triggering failure replanning for team {team_id}: {str(e)}",
                extra={
                    'team_id': team_id,
                    'failed_task_id': failed_task_id,
                    'error': str(e),
                    'action': 'failure_replanning_error'
                },
                exc_info=True
            )
    
    async def handle_user_suggestion_replanning(
        self, 
        team_id: str, 
        user_id: str, 
        suggestion_content: str,
        target_task_ids: List[str] = None
    ) -> Dict[str, Any]:
        """Handle user suggestion for replanning tasks"""
        
        try:
            blackboard = self.get_blackboard(team_id)
            if not blackboard:
                return {
                    "status": "error",
                    "message": "BlackBoard not found for this team"
                }
            
            # Get team info to verify user access
            team = await self.get_team(team_id)
            if not team:
                return {
                    "status": "error", 
                    "message": "Team not found"
                }
            
            # Verify user is team member
            is_team_member = any(member.user_id == user_id for member in team.members)
            if not is_team_member:
                return {
                    "status": "error",
                    "message": "User is not a member of this team"
                }
            
            # Get incomplete tasks to replan
            from app.types.blackboard import TaskFilter, TaskSearchCriteria, TaskStatus
            
            if target_task_ids:
                # User specified specific tasks
                target_tasks = []
                for task_id in target_task_ids:
                    task = await blackboard.get_task(task_id)
                    if task and task.status in [TaskStatus.PENDING, TaskStatus.ASSIGNED, TaskStatus.IN_PROGRESS, TaskStatus.FAILED]:
                        target_tasks.append(task)
            else:
                # Get all incomplete tasks
                incomplete_filter = TaskFilter(
                    status=[TaskStatus.PENDING, TaskStatus.ASSIGNED, TaskStatus.IN_PROGRESS, TaskStatus.FAILED]
                )
                incomplete_criteria = TaskSearchCriteria(filters=incomplete_filter)
                target_tasks, _ = await blackboard.search_tasks(incomplete_criteria)
            
            if not target_tasks:
                return {
                    "status": "warning",
                    "message": "No incomplete tasks found for replanning"
                }
            
            # Create user suggestion replanning task for Jeff
            replanning_task = await blackboard.create_task(
                title=f"用户建议重新规划",
                description=f"用户 {user_id} 建议对当前任务进行重新规划。用户建议内容：{suggestion_content}",
                goal="根据用户建议重新评估和规划相关任务，优化执行策略",
                required_expert_role=ExpertRole.PLANNER,
                creator_id=user_id,
                metadata={
                    "context_data": {
                        "trigger_type": "user_suggestion",
                        "suggestion_content": suggestion_content,
                        "suggested_by": user_id,
                        "target_task_count": len(target_tasks),
                        "target_task_ids": [task.task_id for task in target_tasks]
                    }
                }
            )
            
            # Auto-assign to Jeff (team leader)
            await blackboard.auto_assign_task(replanning_task.task_id)
            
            self.logger.info(
                f"User suggestion replanning task created for team {team_id}",
                extra={
                    'team_id': team_id,
                    'replanning_task_id': replanning_task.task_id,
                    'suggested_by': user_id,
                    'target_task_count': len(target_tasks),
                    'suggestion_content': suggestion_content,
                    'action': 'user_suggestion_replanning_triggered'
                }
            )
            
            return {
                "status": "success",
                "message": "User suggestion replanning task created successfully",
                "replanning_task_id": replanning_task.task_id,
                "target_task_count": len(target_tasks)
            }
            
        except Exception as e:
            self.logger.error(
                f"Error handling user suggestion replanning for team {team_id}: {str(e)}",
                extra={
                    'team_id': team_id,
                    'user_id': user_id,
                    'error': str(e),
                    'action': 'user_suggestion_replanning_error'
                },
                exc_info=True
            )
            return {
                "status": "error",
                "message": f"Error processing user suggestion: {str(e)}"
            }
    
    def _get_max_instances_for_role(self, config: TeamConfiguration, role: ExpertRole) -> int:
        """Get maximum allowed instances for an expert role"""
        
        role_limits = {
            ExpertRole.PLANNER: config.max_jeff_instances,
            ExpertRole.EXECUTOR: config.max_monica_instances,
            ExpertRole.EVALUATOR: config.max_henry_instances
        }
        
        return role_limits.get(role, 1)
    
    async def _store_team(self, team: Team):
        """Store team in Redis"""
        team_key = f"team:{team.team_id}"
        await self._set_redis_value(team_key, team.model_dump_json())
    
    async def _get_all_teams(self) -> List[Team]:
        """Get all teams from Redis"""
        pattern = "team:*"
        team_keys = await self._get_keys_by_pattern(pattern)
        
        teams = []
        for key in team_keys:
            team_data = await self._get_redis_value(key)
            if team_data:
                team = Team.model_validate_json(team_data)
                teams.append(team)
        
        return teams
    
    # === Redis-only Fallback Methods ===
    
    async def _create_team_redis_only(self, team_data: Dict[str, Any]) -> Team:
        """Create team using Redis only (fallback)"""
        team = Team(**team_data)
        
        # Store team in Redis
        team_key = f"team:{team.team_id}"
        await self._set_redis_value(team_key, team.model_dump_json())
        
        # Create BlackBoard instance
        blackboard = BlackBoard(team.team_id)
        self.blackboards[team.team_id] = blackboard
        
        # Initialize expert instances
        await self._initialize_expert_instances(team.team_id)
        
        # Start monitoring service
        await self._start_monitoring_service(team.team_id)
        
        return team
    
    async def _get_team_redis_only(self, team_id: str) -> Optional[Team]:
        """Get team using Redis only (fallback)"""
        team_key = f"team:{team_id}"
        team_data = await self._get_redis_value(team_key)
        
        if team_data:
            return Team.model_validate_json(team_data)
        return None
    
    async def _get_user_teams_redis_only(self, user_id: str) -> List[Team]:
        """Get user teams using Redis only (fallback)"""
        # This would need to be implemented based on your Redis data structure
        # For now, return empty list
        return []
    
    async def _create_expert_instance_redis_only(self, expert_data: Dict[str, Any]) -> ExpertInstance:
        """Create expert instance using Redis only (fallback)"""
        expert = ExpertInstance(**expert_data)
        
        # Store expert in Redis
        expert_key = f"expert:{expert.instance_id}"
        await self._set_redis_value(expert_key, expert.model_dump_json())
        
        return expert
    
    # === Redis Helper Methods ===
    
    async def _set_redis_value(self, key: str, value: str):
        """Set value in Redis"""
        self.redis_client.set(key, value)
    
    async def _get_redis_value(self, key: str) -> Optional[str]:
        """Get value from Redis"""
        return self.redis_client.get(key)
    
    async def _get_keys_by_pattern(self, pattern: str) -> List[str]:
        """Get keys matching pattern"""
        return self.redis_client.keys(pattern) 