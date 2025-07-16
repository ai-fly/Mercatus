from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel

from app.manager import BlackboardManager
from app.types.blackboard import (
    ExpertRole, TaskPriority, TaskStatus, Team, BlackboardTask,
    TaskSearchCriteria, TaskFilter
)
from app.types.output import Platform, Region, ContentType
from app.types.context import AppContext


router = APIRouter(prefix="/blackboard", tags=["BlackBoard"])


# === Request/Response Models ===

class CreateTeamRequest(BaseModel):
    team_name: str
    organization_id: str
    owner_username: str


class CreateMarketingWorkflowRequest(BaseModel):
    project_name: str
    project_description: str
    target_platforms: List[Platform]
    target_regions: List[Region]
    content_types: List[ContentType]
    priority: TaskPriority = TaskPriority.MEDIUM


class CreateTaskRequest(BaseModel):
    title: str
    description: str
    goal: str
    required_expert_role: ExpertRole
    priority: TaskPriority = TaskPriority.MEDIUM
    target_platforms: Optional[List[Platform]] = None
    target_regions: Optional[List[Region]] = None
    content_types: Optional[List[ContentType]] = None
    due_date: Optional[datetime] = None
    metadata: Optional[Dict[str, Any]] = None


class AddCommentRequest(BaseModel):
    content: str
    comment_type: str = "note"


class ScaleExpertsRequest(BaseModel):
    expert_role: ExpertRole
    target_count: int


# === Dependency Functions ===

async def get_blackboard_manager() -> BlackboardManager:
    """Get BlackboardManager instance"""
    # This would be properly injected in a real application
    context = AppContext()  # Placeholder
    return BlackboardManager(context)


# === Team Management Endpoints ===

@router.post("/teams", response_model=Dict[str, Any])
async def create_team(
    request: CreateTeamRequest,
    user_id: str = Query(..., description="User ID of the team creator"),
    manager: BlackboardManager = Depends(get_blackboard_manager)
):
    """Create a new team"""
    
    result = await manager.create_team(
        team_name=request.team_name,
        organization_id=request.organization_id,
        owner_id=user_id,
        owner_username=request.owner_username
    )
    
    if result["status"] == "error":
        raise HTTPException(status_code=400, detail=result["message"])
    
    return result


@router.get("/teams/{team_id}/dashboard", response_model=Dict[str, Any])
async def get_team_dashboard(
    team_id: str,
    manager: BlackboardManager = Depends(get_blackboard_manager)
):
    """Get team dashboard with comprehensive information"""
    
    result = await manager.get_team_dashboard(team_id)
    
    if result["status"] == "error":
        raise HTTPException(status_code=404, detail=result["message"])
    
    return result


@router.get("/teams/{team_id}/analytics", response_model=Dict[str, Any])
async def get_team_analytics(
    team_id: str,
    manager: BlackboardManager = Depends(get_blackboard_manager)
):
    """Get team performance analytics"""
    
    result = await manager.get_team_analytics(team_id)
    
    if result["status"] == "error":
        raise HTTPException(status_code=404, detail=result["message"])
    
    return result


@router.get("/organizations/{organization_id}/overview", response_model=Dict[str, Any])
async def get_organization_overview(
    organization_id: str,
    manager: BlackboardManager = Depends(get_blackboard_manager)
):
    """Get organization-wide overview"""
    
    result = await manager.get_organization_overview(organization_id)
    
    if result["status"] == "error":
        raise HTTPException(status_code=404, detail=result["message"])
    
    return result


# === Task Management Endpoints ===

@router.post("/teams/{team_id}/workflows/marketing", response_model=Dict[str, Any])
async def create_marketing_workflow(
    team_id: str,
    request: CreateMarketingWorkflowRequest,
    creator_id: str = Query(..., description="User ID of the workflow creator"),
    manager: BlackboardManager = Depends(get_blackboard_manager)
):
    """Create a complete marketing workflow"""
    
    result = await manager.create_marketing_workflow(
        team_id=team_id,
        project_name=request.project_name,
        project_description=request.project_description,
        target_platforms=request.target_platforms,
        target_regions=request.target_regions,
        content_types=request.content_types,
        creator_id=creator_id,
        priority=request.priority
    )
    
    if result["status"] == "error":
        raise HTTPException(status_code=400, detail=result["message"])
    
    return result


@router.post("/teams/{team_id}/tasks", response_model=Dict[str, Any])
async def create_task(
    team_id: str,
    request: CreateTaskRequest,
    creator_id: str = Query(..., description="User ID of the task creator"),
    manager: BlackboardManager = Depends(get_blackboard_manager)
):
    """Create a custom task"""
    
    result = await manager.submit_custom_task(
        team_id=team_id,
        title=request.title,
        description=request.description,
        goal=request.goal,
        required_expert_role=request.required_expert_role,
        creator_id=creator_id,
        priority=request.priority,
        target_platforms=request.target_platforms or [],
        target_regions=request.target_regions or [],
        content_types=request.content_types or [],
        due_date=request.due_date,
        metadata=request.metadata or {}
    )
    
    if result["status"] == "error":
        raise HTTPException(status_code=400, detail=result["message"])
    
    return result


@router.post("/teams/{team_id}/tasks/{task_id}/execute", response_model=Dict[str, Any])
async def execute_task(
    team_id: str,
    task_id: str,
    manager: BlackboardManager = Depends(get_blackboard_manager)
):
    """Execute a specific task"""
    
    result = await manager.execute_task(team_id, task_id)
    
    if result["status"] == "error":
        raise HTTPException(status_code=400, detail=result["message"])
    
    return result


@router.get("/teams/{team_id}/tasks", response_model=Dict[str, Any])
async def search_tasks(
    team_id: str,
    query: Optional[str] = Query(None, description="Text search query"),
    status: Optional[List[TaskStatus]] = Query(None, description="Filter by task status"),
    expert_role: Optional[List[ExpertRole]] = Query(None, description="Filter by expert role"),
    priority: Optional[List[TaskPriority]] = Query(None, description="Filter by priority"),
    limit: int = Query(50, ge=1, le=100, description="Number of results to return"),
    offset: int = Query(0, ge=0, description="Number of results to skip"),
    manager: BlackboardManager = Depends(get_blackboard_manager)
):
    """Search tasks with filters"""
    
    result = await manager.search_tasks(
        team_id=team_id,
        query=query,
        status=status,
        expert_role=expert_role,
        priority=priority,
        limit=limit,
        offset=offset
    )
    
    if result["status"] == "error":
        raise HTTPException(status_code=404, detail=result["message"])
    
    return result


@router.get("/teams/{team_id}/tasks/{task_id}", response_model=Dict[str, Any])
async def get_task_details(
    team_id: str,
    task_id: str,
    manager: BlackboardManager = Depends(get_blackboard_manager)
):
    """Get detailed task information"""
    
    result = await manager.get_task_details(team_id, task_id)
    
    if result["status"] == "error":
        raise HTTPException(status_code=404, detail=result["message"])
    
    return result


@router.post("/teams/{team_id}/tasks/{task_id}/comments", response_model=Dict[str, Any])
async def add_task_comment(
    team_id: str,
    task_id: str,
    request: AddCommentRequest,
    author_id: str = Query(..., description="User ID of the comment author"),
    manager: BlackboardManager = Depends(get_blackboard_manager)
):
    """Add a comment to a task"""
    
    result = await manager.add_task_comment(
        team_id=team_id,
        task_id=task_id,
        author_id=author_id,
        content=request.content,
        comment_type=request.comment_type
    )
    
    if result["status"] == "error":
        raise HTTPException(status_code=400, detail=result["message"])
    
    return result


# === Expert Management Endpoints ===

@router.post("/teams/{team_id}/experts/scale", response_model=Dict[str, Any])
async def scale_team_experts(
    team_id: str,
    request: ScaleExpertsRequest,
    manager: BlackboardManager = Depends(get_blackboard_manager)
):
    """Scale expert instances for a specific role"""
    
    result = await manager.scale_team_experts(
        team_id=team_id,
        expert_role=request.expert_role,
        target_count=request.target_count
    )
    
    if result["status"] == "error":
        raise HTTPException(status_code=400, detail=result["message"])
    
    return result


@router.post("/teams/{team_id}/experts/auto-scale", response_model=Dict[str, Any])
async def auto_scale_team(
    team_id: str,
    manager: BlackboardManager = Depends(get_blackboard_manager)
):
    """Automatically scale team based on workload"""
    
    result = await manager.auto_scale_team(team_id)
    
    if result["status"] == "error":
        raise HTTPException(status_code=400, detail=result["message"])
    
    return result


# === System Status Endpoints ===

@router.get("/system/status", response_model=Dict[str, Any])
async def get_system_status(
    manager: BlackboardManager = Depends(get_blackboard_manager)
):
    """Get overall system health status"""
    
    result = await manager.get_system_status()
    
    if result["status"] == "error":
        raise HTTPException(status_code=500, detail=result["message"])
    
    return result


# === Real-time Endpoints ===

@router.get("/teams/{team_id}/tasks/pending", response_model=Dict[str, Any])
async def get_pending_tasks(
    team_id: str,
    manager: BlackboardManager = Depends(get_blackboard_manager)
):
    """Get all pending tasks for a team"""
    
    result = await manager.search_tasks(
        team_id=team_id,
        status=[TaskStatus.PENDING],
        limit=100,
        offset=0
    )
    
    if result["status"] == "error":
        raise HTTPException(status_code=404, detail=result["message"])
    
    return result


@router.get("/teams/{team_id}/tasks/in-progress", response_model=Dict[str, Any])
async def get_in_progress_tasks(
    team_id: str,
    manager: BlackboardManager = Depends(get_blackboard_manager)
):
    """Get all in-progress tasks for a team"""
    
    result = await manager.search_tasks(
        team_id=team_id,
        status=[TaskStatus.IN_PROGRESS],
        limit=100,
        offset=0
    )
    
    if result["status"] == "error":
        raise HTTPException(status_code=404, detail=result["message"])
    
    return result


@router.get("/teams/{team_id}/tasks/completed", response_model=Dict[str, Any])
async def get_completed_tasks(
    team_id: str,
    days: int = Query(7, ge=1, le=30, description="Number of days to look back"),
    manager: BlackboardManager = Depends(get_blackboard_manager)
):
    """Get recently completed tasks for a team"""
    
    result = await manager.search_tasks(
        team_id=team_id,
        status=[TaskStatus.COMPLETED],
        limit=100,
        offset=0
    )
    
    if result["status"] == "error":
        raise HTTPException(status_code=404, detail=result["message"])
    
    return result


# === Batch Operations ===

@router.post("/teams/{team_id}/tasks/batch-assign", response_model=Dict[str, Any])
async def batch_assign_tasks(
    team_id: str,
    task_ids: List[str],
    manager: BlackboardManager = Depends(get_blackboard_manager)
):
    """Batch assign multiple tasks to available experts"""
    
    results = []
    
    for task_id in task_ids:
        try:
            # Get BlackBoard and attempt auto-assignment
            blackboard = manager.team_manager.get_blackboard(team_id)
            if blackboard:
                success = await blackboard.auto_assign_task(task_id)
                results.append({
                    "task_id": task_id,
                    "status": "assigned" if success else "failed",
                    "message": "Auto-assigned successfully" if success else "No available experts"
                })
            else:
                results.append({
                    "task_id": task_id,
                    "status": "failed",
                    "message": "Team not found"
                })
        except Exception as e:
            results.append({
                "task_id": task_id,
                "status": "error",
                "message": str(e)
            })
    
    successful_assignments = len([r for r in results if r["status"] == "assigned"])
    
    return {
        "status": "completed",
        "total_tasks": len(task_ids),
        "successful_assignments": successful_assignments,
        "results": results
    }


# === Statistics Endpoints ===

@router.get("/teams/{team_id}/statistics", response_model=Dict[str, Any])
async def get_team_statistics(
    team_id: str,
    manager: BlackboardManager = Depends(get_blackboard_manager)
):
    """Get comprehensive team statistics"""
    
    # This combines dashboard and analytics data
    dashboard_result = await manager.get_team_dashboard(team_id)
    analytics_result = await manager.get_team_analytics(team_id)
    
    if dashboard_result["status"] == "error":
        raise HTTPException(status_code=404, detail=dashboard_result["message"])
    
    return {
        "status": "success",
        "statistics": {
            "dashboard": dashboard_result.get("dashboard", {}),
            "analytics": analytics_result.get("analytics", {}),
            "generated_at": datetime.now()
        }
    } 