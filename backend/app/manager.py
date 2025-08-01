import asyncio
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any

from app.core.team_manager import team_manager
from app.core.blackboard import BlackBoard
from app.types.blackboard import (
    ExpertRole, TaskPriority, TaskStatus, TaskSearchCriteria, TaskFilter,
    BlackboardTask, Team, ExpertInstance
)
from app.types.output import Platform, Region, ContentType
from app.types.context import AppContext


class BlackboardManager:
    """
    Main manager for the BlackBoard multi-tenant system.
    Provides high-level interface for team collaboration and task management.
    """
    
    def __init__(self, context: AppContext):
        """Initialize BlackboardManager"""
        self.context = context
        self.logger = logging.getLogger("BlackboardManager")
        self.team_manager = team_manager
    
    # === Team Operations ===
    
    async def create_team(
        self,
        team_name: str,
        organization_id: str,
        owner_id: str,
        owner_username: str
    ) -> Dict[str, Any]:
        """Create a new team"""
        
        try:
            team = await self.team_manager.create_team(
                team_name=team_name,
                organization_id=organization_id,
                owner_id=owner_id,
                owner_username=owner_username
            )
            
            return {
                "status": "success",
                "team": team.model_dump(),
                "message": f"Team '{team_name}' created successfully"
            }
            
        except Exception as e:
            self.logger.error(f"Failed to create team: {str(e)}")
            return {
                "status": "error",
                "message": str(e)
            }
    
    async def get_team_dashboard(self, team_id: str) -> Dict[str, Any]:
        """Get comprehensive team dashboard"""
        
        try:
            dashboard = await self.team_manager.get_team_dashboard(team_id)
            
            if not dashboard:
                return {
                    "status": "error",
                    "message": "Team not found"
                }
            
            return {
                "status": "success",
                "dashboard": dashboard
            }
            
        except Exception as e:
            self.logger.error(f"Failed to get team dashboard: {str(e)}")
            return {
                "status": "error",
                "message": str(e)
            }
    
    # === Task Management ===
    
    async def create_marketing_workflow(
        self,
        team_id: str,
        project_name: str,
        project_description: str,
        target_platforms: List[Platform],
        target_regions: List[Region],
        content_types: List[ContentType],
        creator_id: str,
        priority: TaskPriority = TaskPriority.MEDIUM
    ) -> Dict[str, Any]:
        """Create a complete marketing workflow with planning, execution, and review tasks"""
        
        try:
            created_tasks = []
            
            # 1. Create Planning Task (Jeff)
            planning_task = await self.team_manager.submit_task(
                team_id=team_id,
                title=f"Marketing Strategy: {project_name}",
                description=f"Create comprehensive marketing strategy for {project_description}",
                goal="Develop platform-specific marketing strategy with content calendar and campaign structure",
                required_expert_role=ExpertRole.PLANNER,
                creator_id=creator_id,
                priority=priority,
                target_platforms=target_platforms,
                target_regions=target_regions,
                content_types=content_types,
                metadata={
                    "project_name": project_name,
                    "workflow_type": "marketing",
                    "required_skills": ["strategy", "planning", "market_analysis"]
                }
            )
            
            if planning_task:
                created_tasks.append(planning_task)
            
            # 2. Create Content Generation Task (Monica) - depends on planning
            content_task = await self.team_manager.submit_task(
                team_id=team_id,
                title=f"Content Creation: {project_name}",
                description=f"Generate platform-adapted content based on marketing strategy for {project_description}",
                goal="Create high-quality, platform-optimized content using marketing techniques",
                required_expert_role=ExpertRole.EXECUTOR,
                creator_id=creator_id,
                priority=priority,
                target_platforms=target_platforms,
                target_regions=target_regions,
                content_types=content_types,
                metadata={
                    "project_name": project_name,
                    "workflow_type": "content_generation",
                    "required_skills": ["content_creation", "copywriting", "marketing_techniques"],
                    "depends_on": planning_task.task_id if planning_task else None
                }
            )
            
            if content_task:
                created_tasks.append(content_task)
            
            # 3. Create Review Task (Henry) - depends on content
            review_task = await self.team_manager.submit_task(
                team_id=team_id,
                title=f"Content Review: {project_name}",
                description=f"Review content for compliance and quality assurance for {project_description}",
                goal="Ensure content meets platform policies and regional compliance requirements",
                required_expert_role=ExpertRole.EVALUATOR,
                creator_id=creator_id,
                priority=priority,
                target_platforms=target_platforms,
                target_regions=target_regions,
                content_types=content_types,
                metadata={
                    "project_name": project_name,
                    "workflow_type": "compliance_review",
                    "required_skills": ["compliance", "legal_review", "quality_assurance"],
                    "depends_on": content_task.task_id if content_task else None
                }
            )
            
            if review_task:
                created_tasks.append(review_task)
            
            return {
                "status": "success",
                "workflow_id": f"workflow_{project_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                "tasks_created": len(created_tasks),
                "tasks": [task.model_dump() for task in created_tasks],
                "message": f"Marketing workflow created for '{project_name}'"
            }
            
        except Exception as e:
            self.logger.error(f"Failed to create marketing workflow: {str(e)}")
            return {
                "status": "error",
                "message": str(e)
            }
    
    async def submit_custom_task(
        self,
        team_id: str,
        title: str,
        description: str,
        goal: str,
        required_expert_role: ExpertRole,
        creator_id: str,
        priority: TaskPriority = TaskPriority.MEDIUM,
        **kwargs
    ) -> Dict[str, Any]:
        """Submit a custom task"""
        
        try:
            task = await self.team_manager.submit_task(
                team_id=team_id,
                title=title,
                description=description,
                goal=goal,
                required_expert_role=required_expert_role,
                creator_id=creator_id,
                priority=priority,
                **kwargs
            )
            
            if task:
                return {
                    "status": "success",
                    "task": task.model_dump(),
                    "message": f"Task '{title}' created successfully"
                }
            else:
                return {
                    "status": "error",
                    "message": "Failed to create task"
                }
                
        except Exception as e:
            self.logger.error(f"Failed to submit custom task: {str(e)}")
            return {
                "status": "error",
                "message": str(e)
            }
    
    async def execute_task(self, team_id: str, task_id: str) -> Dict[str, Any]:
        """Execute a specific task"""
        
        try:
            result = await self.team_manager.execute_task(team_id, task_id)
            return result
            
        except Exception as e:
            self.logger.error(f"Failed to execute task: {str(e)}")
            return {
                "status": "error",
                "message": str(e)
            }
    
    # === Task Queries ===
    
    async def search_tasks(
        self,
        team_id: str,
        query: Optional[str] = None,
        status: Optional[List[TaskStatus]] = None,
        expert_role: Optional[List[ExpertRole]] = None,
        priority: Optional[List[TaskPriority]] = None,
        limit: int = 50,
        offset: int = 0
    ) -> Dict[str, Any]:
        """Search tasks with filters"""
        
        try:
            blackboard = self.team_manager.get_blackboard(team_id)
            if not blackboard:
                return {
                    "status": "error",
                    "message": "Team not found"
                }
            
            # Build search criteria
            filters = TaskFilter(
                status=status,
                expert_role=expert_role,
                priority=priority
            )
            
            criteria = TaskSearchCriteria(
                query=query,
                filters=filters,
                limit=limit,
                offset=offset
            )
            
            tasks, total_count = await blackboard.search_tasks(criteria)
            
            return {
                "status": "success",
                "tasks": [task.model_dump() for task in tasks],
                "total_count": total_count,
                "page_info": {
                    "limit": limit,
                    "offset": offset,
                    "has_more": (offset + limit) < total_count
                }
            }
            
        except Exception as e:
            self.logger.error(f"Failed to search tasks: {str(e)}")
            return {
                "status": "error",
                "message": str(e)
            }
    
    async def get_task_details(self, team_id: str, task_id: str) -> Dict[str, Any]:
        """Get detailed task information"""
        
        try:
            blackboard = self.team_manager.get_blackboard(team_id)
            if not blackboard:
                return {
                    "status": "error",
                    "message": "Team not found"
                }
            
            task = await blackboard.get_task(task_id)
            if not task:
                return {
                    "status": "error",
                    "message": "Task not found"
                }
            
            # Get task comments
            comments = await blackboard.get_task_comments(task_id)
            
            return {
                "status": "success",
                "task": task.model_dump(),
                "comments": [comment.model_dump() for comment in comments]
            }
            
        except Exception as e:
            self.logger.error(f"Failed to get task details: {str(e)}")
            return {
                "status": "error",
                "message": str(e)
            }
    
    # === Expert Management ===
    
    async def scale_team_experts(
        self,
        team_id: str,
        expert_role: ExpertRole,
        target_count: int
    ) -> Dict[str, Any]:
        """Scale expert instances for a role"""
        
        try:
            success = await self.team_manager.scale_experts(team_id, expert_role, target_count)
            
            if success:
                return {
                    "status": "success",
                    "message": f"Scaled {expert_role.value} instances to {target_count}"
                }
            else:
                return {
                    "status": "error",
                    "message": "Failed to scale experts"
                }
                
        except Exception as e:
            self.logger.error(f"Failed to scale experts: {str(e)}")
            return {
                "status": "error",
                "message": str(e)
            }
    
    async def auto_scale_team(self, team_id: str) -> Dict[str, Any]:
        """Automatically scale team based on workload"""
        
        try:
            result = await self.team_manager.auto_scale_team(team_id)
            return result
            
        except Exception as e:
            self.logger.error(f"Failed to auto-scale team: {str(e)}")
            return {
                "status": "error",
                "message": str(e)
            }
    
    # === Collaboration Features ===
    
    async def add_task_comment(
        self,
        team_id: str,
        task_id: str,
        author_id: str,
        content: str,
        comment_type: str = "note"
    ) -> Dict[str, Any]:
        """Add a comment to a task"""
        
        try:
            blackboard = self.team_manager.get_blackboard(team_id)
            if not blackboard:
                return {
                    "status": "error",
                    "message": "Team not found"
                }
            
            comment = await blackboard.add_comment(
                task_id=task_id,
                author_id=author_id,
                content=content,
                comment_type=comment_type
            )
            
            return {
                "status": "success",
                "comment": comment.model_dump(),
                "message": "Comment added successfully"
            }
            
        except Exception as e:
            self.logger.error(f"Failed to add comment: {str(e)}")
            return {
                "status": "error",
                "message": str(e)
            }
    
    # === Analytics and Reporting ===
    
    async def get_team_analytics(self, team_id: str) -> Dict[str, Any]:
        """Get team performance analytics"""
        
        try:
            blackboard = self.team_manager.get_blackboard(team_id)
            if not blackboard:
                return {
                    "status": "error",
                    "message": "Team not found"
                }
            
            performance = await blackboard.get_team_performance_metrics()
            
            return {
                "status": "success",
                "analytics": performance
            }
            
        except Exception as e:
            self.logger.error(f"Failed to get team analytics: {str(e)}")
            return {
                "status": "error",
                "message": str(e)
            }
    
    async def get_organization_overview(self, organization_id: str) -> Dict[str, Any]:
        """Get organization-wide overview"""
        
        try:
            overview = await self.team_manager.get_organization_overview(organization_id)
            
            return {
                "status": "success",
                "overview": overview
            }
            
        except Exception as e:
            self.logger.error(f"Failed to get organization overview: {str(e)}")
            return {
                "status": "error",
                "message": str(e)
            }
    
    # === Health Check and Status ===
    
    async def get_system_status(self) -> Dict[str, Any]:
        """Get overall system health status"""
        
        try:
            # Get team counts
            all_teams = await self.team_manager._get_all_teams()
            active_teams = len([team for team in all_teams if team.is_active])
            
            # Get task statistics
            total_tasks = 0
            total_experts = 0
            
            for team in all_teams:
                blackboard = self.team_manager.get_blackboard(team.team_id)
                if blackboard:
                    state = await blackboard.get_blackboard_state()
                    total_tasks += state.total_tasks
                total_experts += len(team.expert_instances)
            
            return {
                "status": "success",
                "system_health": {
                    "total_teams": len(all_teams),
                    "active_teams": active_teams,
                    "total_experts": total_experts,
                    "total_tasks": total_tasks,
                    "timestamp": datetime.now(),
                    "version": "1.0.0"
                }
            }
            
        except Exception as e:
            self.logger.error(f"Failed to get system status: {str(e)}")
            return {
                "status": "error",
                "message": str(e)
            }


class AgentManager:
    """Legacy agent manager for backwards compatibility"""
    
    def __init__(self, context: AppContext):
        self.context = context
        self.blackboard_manager = BlackboardManager(context)
        self.logger = logging.getLogger("AgentManager")
    
    async def run(self, input_data: dict) -> dict:
        """Run agent workflow - updated to use BlackBoard system"""
        
        try:
            # Extract team information from input
            team_id = input_data.get("team_id")
            if not team_id:
                return {
                    "status": "error",
                    "error": "team_id required"
                }
            
            # Determine workflow type
            workflow_type = input_data.get("workflow_type", "custom")
            
            if workflow_type == "marketing":
                # Create marketing workflow
                result = await self.blackboard_manager.create_marketing_workflow(
                    team_id=team_id,
                    project_name=input_data.get("project_name", "Marketing Project"),
                    project_description=input_data.get("description", ""),
                    target_platforms=input_data.get("target_platforms", []),
                    target_regions=input_data.get("target_regions", []),
                    content_types=input_data.get("content_types", []),
                    creator_id=input_data.get("creator_id", "system"),
                    priority=TaskPriority(input_data.get("priority", "medium"))
                )
            else:
                # Create custom task
                result = await self.blackboard_manager.submit_custom_task(
                    team_id=team_id,
                    title=input_data.get("title", "Custom Task"),
                    description=input_data.get("description", ""),
                    goal=input_data.get("goal", ""),
                    required_expert_role=ExpertRole(input_data.get("expert_role", "planner")),
                    creator_id=input_data.get("creator_id", "system"),
                    priority=TaskPriority(input_data.get("priority", "medium"))
                )
            
            return result
            
        except Exception as e:
            self.logger.error(f"Agent workflow error: {str(e)}")
            return {
                "status": "error",
                "error": str(e)
            }