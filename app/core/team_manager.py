import asyncio
import logging
from datetime import datetime
from typing import Dict, List, Optional, Type, Any
from uuid import uuid4

from app.types.blackboard import (
    Team, TeamMember, TeamRole, TeamConfiguration, ExpertInstance, ExpertRole,
    BlackboardTask, TaskStatus, TaskPriority, TaskSearchCriteria, TaskFilter
)
from app.core.blackboard import BlackBoard
from app.experts.expert import ExpertBase
from app.experts.plan_expert import PlanExpert
from app.experts.content_expert import ContentExpert
from app.experts.rewiew_expert import ReviewExpert
from app.clients.redis_client import redis_client_instance
from app.config import settings
from app.utils.logging import get_business_logger, get_performance_logger


class TeamManager:
    """
    Multi-tenant team management system that coordinates BlackBoard instances,
    expert instances, and team collaboration for the Mercatus content factory.
    """
    
    def __init__(self):
        """Initialize TeamManager"""
        self.redis_client = redis_client_instance.get_redis_client()
        self.logger = logging.getLogger("TeamManager")
        self.business_logger = get_business_logger()
        self.performance_logger = get_performance_logger()
        
        self.teams: Dict[str, Team] = {}
        self.blackboards: Dict[str, BlackBoard] = {}
        self.expert_instances: Dict[str, Dict[str, ExpertBase]] = {}  # team_id -> instance_id -> expert
        
        # Expert class mapping
        self.expert_classes = {
            ExpertRole.PLANNER: PlanExpert,
            ExpertRole.EXECUTOR: ContentExpert,
            ExpertRole.EVALUATOR: ReviewExpert
        }
        
        self.logger.info("TeamManager initialized successfully")
    
    # === Team Management ===
    
    async def create_team(
        self,
        team_name: str,
        organization_id: str,
        owner_id: str,
        owner_username: str
    ) -> Team:
        """Create a new team"""
        
        with self.performance_logger.time_operation(
            "create_team",
            organization_id=organization_id,
            owner_id=owner_id
        ):
            self.logger.debug(
                f"Creating team: {team_name} for organization {organization_id}",
                extra={
                    'team_name': team_name,
                    'organization_id': organization_id,
                    'user_id': owner_id,
                    'action': 'team_creation_start'
                }
            )
            
            team = Team(
                team_id=str(uuid4()),
                team_name=team_name,
                organization_id=organization_id,
                owner_id=owner_id,
                configuration=TeamConfiguration()
            )
            
            # Add owner as team member
            owner_member = TeamMember(
                user_id=owner_id,
                username=owner_username,
                role=TeamRole.OWNER
            )
            team.members.append(owner_member)
            
            # Store team
            await self._store_team(team)
            self.teams[team.team_id] = team
            
            # Create default expert instances
            await self._initialize_team_experts(team)
            
            self.logger.info(
                f"Created team {team.team_id}: {team_name}",
                extra={
                    'team_id': team.team_id,
                    'team_name': team_name,
                    'organization_id': organization_id,
                    'owner_id': owner_id,
                    'member_count': len(team.members),
                    'expert_count': len(team.expert_instances),
                    'action': 'team_created'
                }
            )
            
            return team
    
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
        """Get team by ID"""
        
        if team_id in self.teams:
            return self.teams[team_id]
        
        # Load from Redis
        team_data = await self._get_redis_value(f"team:{team_id}")
        if team_data:
            team = Team.model_validate_json(team_data)
            self.teams[team_id] = team
            return team
        
        return None
    
    async def get_user_teams(self, user_id: str) -> List[Team]:
        """Get all teams a user belongs to"""
        
        all_teams = await self._get_all_teams()
        user_teams = []
        
        for team in all_teams:
            for member in team.members:
                if member.user_id == user_id:
                    user_teams.append(team)
                    break
        
        return user_teams
    
    # === Expert Instance Management ===
    
    async def create_expert_instance(
        self,
        team_id: str,
        expert_role: ExpertRole,
        instance_name: Optional[str] = None,
        max_concurrent_tasks: int = 3,
        specializations: List[str] = None
    ) -> Optional[ExpertInstance]:
        """Create a new expert instance for a team"""
        
        with self.performance_logger.time_operation(
            "create_expert_instance",
            team_id=team_id,
            expert_role=expert_role.value
        ):
            team = await self.get_team(team_id)
            if not team:
                self.logger.error(
                    f"Cannot create expert for team {team_id}: team not found",
                    extra={'team_id': team_id, 'expert_role': expert_role.value}
                )
                return None
            
            # Check team limits
            current_count = len([e for e in team.expert_instances if e.expert_role == expert_role])
            max_count = self._get_max_instances_for_role(team.configuration, expert_role)
            
            if current_count >= max_count:
                self.logger.warning(
                    f"Team {team_id} at max {expert_role.value} instances ({max_count})",
                    extra={
                        'team_id': team_id,
                        'expert_role': expert_role.value,
                        'current_count': current_count,
                        'max_count': max_count,
                        'action': 'expert_creation_limit_reached'
                    }
                )
                return None
            
            # Generate instance name if not provided
            if not instance_name:
                instance_name = f"{expert_role.value.title()} {current_count + 1}"
            
            # Create expert instance metadata
            instance = ExpertInstance(
                instance_id=str(uuid4()),
                expert_role=expert_role,
                instance_name=instance_name,
                status="active",
                max_concurrent_tasks=max_concurrent_tasks,
                specializations=specializations or []
            )
            
            # Create actual expert object
            expert_class = self.expert_classes[expert_role]
            expert_obj = expert_class(index=current_count + 1)
            
            # Store in team
            team.expert_instances.append(instance)
            team.updated_at = datetime.now()
            await self._store_team(team)
            
            # Store expert instance in memory
            if team_id not in self.expert_instances:
                self.expert_instances[team_id] = {}
            self.expert_instances[team_id][instance.instance_id] = expert_obj
            
            # Register with BlackBoard
            blackboard = self.get_blackboard(team_id)
            if blackboard:
                await blackboard.register_expert_instance(
                    expert_role, instance_name, max_concurrent_tasks, specializations
                )
            
            self.logger.info(
                f"Created expert instance {instance.instance_id}: {instance_name}",
                extra={
                    'team_id': team_id,
                    'expert_instance_id': instance.instance_id,
                    'expert_role': expert_role.value,
                    'instance_name': instance_name,
                    'max_concurrent_tasks': max_concurrent_tasks,
                    'specializations': specializations or [],
                    'total_experts': len(team.expert_instances),
                    'action': 'expert_instance_created'
                }
            )
            
            return instance
    
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
            blackboard = BlackBoard(team_id)
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
        """Execute a task using assigned expert instance"""
        
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
    
    # === Helper Methods ===
    
    async def _initialize_team_experts(self, team: Team):
        """Initialize default expert instances for a new team"""
        
        # Create initial Jeff instances (planners)
        for i in range(1):  # Start with 1 Jeff
            await self.create_expert_instance(
                team.team_id,
                ExpertRole.PLANNER,
                f"Jeff {i+1}",
                max_concurrent_tasks=3
            )
        
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


# Global team manager instance
team_manager = TeamManager() 