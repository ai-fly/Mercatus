import logging
import time
from datetime import datetime
from typing import Dict, List, Optional, Any
from fastapi import APIRouter, HTTPException, Depends, Request, Response
from pydantic import BaseModel

from app.core.team_manager import TeamManager
from app.services.hybrid_storage import HybridStorageService
from app.dependencies import get_team_manager, get_hybrid_storage_service
from app.types.blackboard import (
    Team, TeamMember, TeamRole, ExpertInstance, ExpertRole,
    BlackboardTask, TaskStatus, TaskPriority, TaskSearchCriteria,
    Platform, Region, ContentType
)
from app.utils.logging import get_business_logger, get_performance_logger

# 创建路由器
router = APIRouter()

# 日志记录器
logger = logging.getLogger("BlackboardController")
business_logger = get_business_logger()
performance_logger = get_performance_logger()


# === Team Management Endpoints ===

@router.post("/teams", response_model=Dict[str, Any])
async def create_team(
    request: Request,
    team_data: dict,
    team_manager: TeamManager = Depends(get_team_manager),
    hybrid_storage: HybridStorageService = Depends(get_hybrid_storage_service)
):
    """Create a new team"""
    
    with performance_logger.time_operation(
        "api_create_team",
        team_name=team_data.get("team_name"),
    ):
        try:
            team = await team_manager.create_team(
                team_name=team_data["team_name"],
                description=team_data.get("description"),
                owner_id=team_data["owner_id"],
                owner_username=team_data["owner_username"]
            )
            
            business_logger.log_team_created(
                team.team_id,
                team.team_name,
                team.owner_id
            )
            
            return {
                "status": "success",
                "team_id": team.team_id,
                "message": "Team created successfully"
            }
            
        except Exception as e:
            logger.error(f"Failed to create team: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))


@router.get("/teams/{team_id}", response_model=Dict[str, Any])
async def get_team(
    request: Request,
    team_id: str,
    team_manager: TeamManager = Depends(get_team_manager)
):
    """Get team by ID"""
    
    try:
        team = await team_manager.get_team(team_id)
        if not team:
            raise HTTPException(status_code=404, detail="Team not found")
        
        return {
            "status": "success",
            "team": team.model_dump()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get team {team_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/users/{user_id}/teams", response_model=Dict[str, Any])
async def get_user_teams(
    request: Request,
    user_id: str,
    team_manager: TeamManager = Depends(get_team_manager)
):
    """Get all teams for a user"""
    
    try:
        teams = await team_manager.get_user_teams(user_id)
        
        return {
            "status": "success",
            "teams": [team.model_dump() for team in teams],
            "count": len(teams)
        }
        
    except Exception as e:
        logger.error(f"Failed to get user teams: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# === Expert Instance Management Endpoints ===

# 专家实例的创建已在团队创建时自动完成，无需单独接口。

@router.get("/teams/{team_id}/experts", response_model=Dict[str, Any])
async def get_team_experts(
    request: Request,
    team_id: str,
    role: Optional[str] = None,
    team_manager: TeamManager = Depends(get_team_manager)
):
    """Get team expert instances"""
    
    try:
        expert_role = ExpertRole(role) if role else None
        experts = await team_manager.get_team_experts(expert_role)
        
        return {
            "status": "success",
            "experts": [expert.model_dump() for expert in experts],
            "count": len(experts)
        }
        
    except Exception as e:
        logger.error(f"Failed to get team experts: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# === Task Management Endpoints ===

@router.post("/teams/{team_id}/tasks", response_model=Dict[str, Any])
async def create_task(
    request: Request,
    team_id: str,
    task_data: dict,
    team_manager: TeamManager = Depends(get_team_manager)
):
    """Create a new task"""
    
    with performance_logger.time_operation(
        "api_create_task",
        team_id=team_id,
        expert_role=task_data.get("required_expert_role")
    ):
        try:
            result = await team_manager.submit_custom_task(
                team_id=team_id,
                title=task_data["title"],
                description=task_data["description"],
                goal=task_data["goal"],
                required_expert_role=ExpertRole(task_data["required_expert_role"]),
                creator_id=task_data["creator_id"],
                priority=TaskPriority(task_data.get("priority", "medium")),
                target_platforms=task_data.get("target_platforms", []),
                target_regions=task_data.get("target_regions", []),
                content_types=task_data.get("content_types", [])
            )
            
            if result["status"] == "success":
                business_logger.log_task_created(
                    result["task_id"],
                    task_data["title"],
                    team_id,
                    task_data["creator_id"],
                    task_data.get("priority", "medium")
                )
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to create task: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))


@router.get("/teams/{team_id}/tasks", response_model=Dict[str, Any])
async def get_team_tasks(
    request: Request,
    team_id: str,
    status: Optional[str] = None,
    team_manager: TeamManager = Depends()
):
    """Get team tasks"""
    
    try:
        blackboard = team_manager.get_blackboard(team_id)
        if not blackboard:
            raise HTTPException(status_code=404, detail="Team not found")
        
        if status:
            tasks = await blackboard.get_tasks_by_status(TaskStatus(status))
        else:
            # Get all tasks
            all_tasks = []
            for task_status in TaskStatus:
                tasks = await blackboard.get_tasks_by_status(task_status)
                all_tasks.extend(tasks)
            tasks = all_tasks
        
        return {
            "status": "success",
            "tasks": [task.model_dump() for task in tasks],
            "count": len(tasks)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get team tasks: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/teams/{team_id}/tasks/{task_id}", response_model=Dict[str, Any])
async def get_task(
    request: Request,
    team_id: str,
    task_id: str,
    team_manager: TeamManager = Depends()
):
    """Get task by ID"""
    
    try:
        blackboard = team_manager.get_blackboard(team_id)
        if not blackboard:
            raise HTTPException(status_code=404, detail="Team not found")
        
        task = await blackboard.get_task(task_id)
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")
        
        return {
            "status": "success",
            "task": task.model_dump()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get task: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/teams/{team_id}/tasks/{task_id}/execute", response_model=Dict[str, Any])
async def execute_task(
    request: Request,
    team_id: str,
    task_id: str,
    team_manager: TeamManager = Depends()
):
    """Execute a task"""
    
    with performance_logger.time_operation(
        "api_execute_task",
        team_id=team_id,
        task_id=task_id
    ):
        try:
            result = await team_manager.execute_task(team_id, task_id)
            return result
            
        except Exception as e:
            logger.error(f"Failed to execute task: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))


# === Planning and Replanning Endpoints ===

@router.post("/teams/{team_id}/planning/user-suggestion", response_model=Dict[str, Any])
async def submit_user_suggestion_replanning(
    request: Request,
    team_id: str,
    suggestion_data: dict,
    team_manager: TeamManager = Depends()
):
    """Submit user suggestion for task replanning"""
    
    try:
        blackboard = team_manager.get_blackboard(team_id)
        if not blackboard:
            raise HTTPException(status_code=404, detail="Team not found")
        
        # Create replanning task
        replanning_task = await blackboard.create_task(
            title=f"Replanning based on user suggestion: {suggestion_data.get('suggestion_content', '')[:50]}...",
            description=f"User suggestion: {suggestion_data.get('suggestion_content', '')}",
            goal="Replan tasks based on user feedback",
            required_expert_role=ExpertRole.PLANNER,
            creator_id=suggestion_data.get("user_id", "system"),
            priority=TaskPriority.HIGH,
            metadata={
                "planning_trigger": "user_suggestion",
                "original_suggestion": suggestion_data.get("suggestion_content"),
                "target_task_ids": suggestion_data.get("target_task_ids", [])
            }
        )
        
        business_logger.log_replanning_triggered(
            replanning_task.task_id,
            team_id,
            "user_suggestion",
            suggestion_data.get("user_id", "system")
        )
        
        return {
            "status": "success",
            "replanning_task_id": replanning_task.task_id,
            "message": "Replanning task created successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to submit user suggestion: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# === Team Performance Endpoints ===

@router.get("/teams/{team_id}/performance", response_model=Dict[str, Any])
async def get_team_performance(
    request: Request,
    team_id: str,
    team_manager: TeamManager = Depends()
):
    """Get team performance metrics"""
    
    try:
        blackboard = team_manager.get_blackboard(team_id)
        if not blackboard:
            raise HTTPException(status_code=404, detail="Team not found")
        
        metrics = await blackboard.get_team_performance_metrics()
        
        return {
            "status": "success",
            "metrics": metrics
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get team performance: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# === BlackBoard State Endpoints ===

@router.get("/teams/{team_id}/blackboard/state", response_model=Dict[str, Any])
async def get_blackboard_state(
    request: Request,
    team_id: str,
    team_manager: TeamManager = Depends()
):
    """Get BlackBoard state"""
    
    try:
        blackboard = team_manager.get_blackboard(team_id)
        if not blackboard:
            raise HTTPException(status_code=404, detail="Team not found")
        
        state = await blackboard.get_blackboard_state()
        
        return {
            "status": "success",
            "state": state.model_dump()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get BlackBoard state: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e)) 