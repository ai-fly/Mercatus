import logging
import time
from datetime import datetime
from typing import Dict, List, Optional, Any
from fastapi import APIRouter, HTTPException, Depends, Request, Response
from pydantic import BaseModel

from app.manager import BlackboardManager
from app.types.blackboard import ExpertRole, TaskPriority, TaskStatus
from app.types.output import Platform, Region, ContentType
from app.types.context import AppContext
from app.utils.logging import get_performance_logger, get_business_logger

# 创建API日志记录器
api_logger = logging.getLogger("MercatusAPI")
performance_logger = get_performance_logger()
business_logger = get_business_logger()

router = APIRouter(prefix="/api/v1", tags=["BlackBoard"])

# === 依赖注入 ===

def get_blackboard_manager() -> BlackboardManager:
    """Get BlackBoard manager instance"""
    context = AppContext()
    return BlackboardManager(context)

# === 日志中间件函数 ===

def log_api_request(request: Request, body: Any = None) -> str:
    """记录API请求信息"""
    request_id = f"req_{int(time.time() * 1000)}"
    
    api_logger.info(
        f"API Request: {request.method} {request.url.path}",
        extra={
            'request_id': request_id,
            'method': request.method,
            'path': request.url.path,
            'query_params': dict(request.query_params),
            'client_ip': request.client.host if request.client else 'unknown',
            'user_agent': request.headers.get('user-agent', 'unknown'),
            'content_type': request.headers.get('content-type', 'unknown'),
            'request_body': body if body else None,
            'action': 'api_request'
        }
    )
    
    return request_id

def log_api_response(request_id: str, status_code: int, response_data: Any, execution_time: float):
    """记录API响应信息"""
    
    log_level = logging.INFO
    if status_code >= 400:
        log_level = logging.ERROR if status_code >= 500 else logging.WARNING
    
    api_logger.log(
        log_level,
        f"API Response: {status_code}",
        extra={
            'request_id': request_id,
            'status_code': status_code,
            'execution_time': execution_time,
            'response_size': len(str(response_data)) if response_data else 0,
            'success': status_code < 400,
            'action': 'api_response'
        }
    )

# === 请求/响应模型 ===

class CreateTeamRequest(BaseModel):
    team_name: str
    organization_id: str
    owner_username: str

class CreateTaskRequest(BaseModel):
    title: str
    description: str
    goal: str
    required_expert_role: ExpertRole
    priority: TaskPriority = TaskPriority.MEDIUM
    target_platforms: Optional[List[Platform]] = None
    target_regions: Optional[List[Region]] = None
    content_types: Optional[List[ContentType]] = None

class CreateMarketingWorkflowRequest(BaseModel):
    project_name: str
    project_description: str
    target_platforms: List[Platform]
    target_regions: List[Region]
    content_types: List[ContentType]
    priority: TaskPriority = TaskPriority.MEDIUM

# === API端点 ===

@router.post("/teams", response_model=Dict[str, Any])
async def create_team(
    request: Request,
    team_data: CreateTeamRequest,
    manager: BlackboardManager = Depends(get_blackboard_manager)
):
    """Create a new team"""
    start_time = time.time()
    request_id = log_api_request(request, team_data.model_dump())
    
    try:
        with performance_logger.time_operation(
            "api_create_team",
            request_id=request_id,
            organization_id=team_data.organization_id
        ):
            # 提取用户ID（在实际实现中应该从认证token中获取）
            user_id = request.headers.get('X-User-ID', 'anonymous')
            
            business_logger.logger.info(
                f"Creating team request from user {user_id}",
                extra={
                    'request_id': request_id,
                    'user_id': user_id,
                    'team_name': team_data.team_name,
                    'organization_id': team_data.organization_id,
                    'action': 'team_creation_request'
                }
            )
            
            result = await manager.create_team(
                team_name=team_data.team_name,
                organization_id=team_data.organization_id,
                owner_id=user_id,
                owner_username=team_data.owner_username
            )
            
            execution_time = time.time() - start_time
            log_api_response(request_id, 200, result, execution_time)
            
            return result
    
    except Exception as e:
        execution_time = time.time() - start_time
        api_logger.error(
            f"Team creation failed: {str(e)}",
            extra={
                'request_id': request_id,
                'error_type': type(e).__name__,
                'error_message': str(e),
                'execution_time': execution_time,
                'action': 'api_error'
            },
            exc_info=True
        )
        log_api_response(request_id, 500, None, execution_time)
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/teams/{team_id}/tasks", response_model=Dict[str, Any])
async def create_task(
    request: Request,
    team_id: str,
    task_data: CreateTaskRequest,
    manager: BlackboardManager = Depends(get_blackboard_manager)
):
    """Create a new task for a team"""
    start_time = time.time()
    request_id = log_api_request(request, {**task_data.model_dump(), "team_id": team_id})
    
    try:
        with performance_logger.time_operation(
            "api_create_task",
            request_id=request_id,
            team_id=team_id,
            expert_role=task_data.required_expert_role.value
        ):
            user_id = request.headers.get('X-User-ID', 'anonymous')
            
            business_logger.logger.info(
                f"Creating task request from user {user_id}",
                extra={
                    'request_id': request_id,
                    'user_id': user_id,
                    'team_id': team_id,
                    'task_title': task_data.title,
                    'expert_role': task_data.required_expert_role.value,
                    'priority': task_data.priority.value,
                    'action': 'task_creation_request'
                }
            )
            
            result = await manager.submit_custom_task(
                team_id=team_id,
                title=task_data.title,
                description=task_data.description,
                goal=task_data.goal,
                required_expert_role=task_data.required_expert_role,
                creator_id=user_id,
                priority=task_data.priority,
                target_platforms=task_data.target_platforms or [],
                target_regions=task_data.target_regions or [],
                content_types=task_data.content_types or []
            )
            
            execution_time = time.time() - start_time
            log_api_response(request_id, 200, result, execution_time)
            
            return result
    
    except Exception as e:
        execution_time = time.time() - start_time
        api_logger.error(
            f"Task creation failed: {str(e)}",
            extra={
                'request_id': request_id,
                'team_id': team_id,
                'error_type': type(e).__name__,
                'error_message': str(e),
                'execution_time': execution_time,
                'action': 'api_error'
            },
            exc_info=True
        )
        log_api_response(request_id, 500, None, execution_time)
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/teams/{team_id}/tasks/{task_id}/execute", response_model=Dict[str, Any])
async def execute_task(
    request: Request,
    team_id: str,
    task_id: str,
    manager: BlackboardManager = Depends(get_blackboard_manager)
):
    """Execute a specific task"""
    start_time = time.time()
    request_id = log_api_request(request, {"team_id": team_id, "task_id": task_id})
    
    try:
        with performance_logger.time_operation(
            "api_execute_task",
            request_id=request_id,
            team_id=team_id,
            task_id=task_id
        ):
            user_id = request.headers.get('X-User-ID', 'anonymous')
            
            business_logger.logger.info(
                f"Task execution request from user {user_id}",
                extra={
                    'request_id': request_id,
                    'user_id': user_id,
                    'team_id': team_id,
                    'task_id': task_id,
                    'action': 'task_execution_request'
                }
            )
            
            result = await manager.execute_task(team_id, task_id)
            
            execution_time = time.time() - start_time
            
            # 根据结果状态设置HTTP状态码
            if result.get("status") == "error":
                status_code = 400
                log_api_response(request_id, status_code, result, execution_time)
                raise HTTPException(status_code=status_code, detail=result.get("message", "Task execution failed"))
            
            log_api_response(request_id, 200, result, execution_time)
            
            # 记录任务执行结果
            business_logger.logger.info(
                f"Task execution completed",
                extra={
                    'request_id': request_id,
                    'user_id': user_id,
                    'team_id': team_id,
                    'task_id': task_id,
                    'execution_status': result.get('status', 'unknown'),
                    'execution_time': execution_time,
                    'action': 'task_execution_completed'
                }
            )
            
            return result
    
    except HTTPException:
        raise
    except Exception as e:
        execution_time = time.time() - start_time
        api_logger.error(
            f"Task execution failed: {str(e)}",
            extra={
                'request_id': request_id,
                'team_id': team_id,
                'task_id': task_id,
                'error_type': type(e).__name__,
                'error_message': str(e),
                'execution_time': execution_time,
                'action': 'api_error'
            },
            exc_info=True
        )
        log_api_response(request_id, 500, None, execution_time)
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/teams/{team_id}/workflows/marketing", response_model=Dict[str, Any])
async def create_marketing_workflow(
    request: Request,
    team_id: str,
    workflow_data: CreateMarketingWorkflowRequest,
    manager: BlackboardManager = Depends(get_blackboard_manager)
):
    """Create a complete marketing workflow"""
    start_time = time.time()
    request_id = log_api_request(request, {**workflow_data.model_dump(), "team_id": team_id})
    
    try:
        with performance_logger.time_operation(
            "api_create_marketing_workflow",
            request_id=request_id,
            team_id=team_id,
            project_name=workflow_data.project_name
        ):
            user_id = request.headers.get('X-User-ID', 'anonymous')
            
            business_logger.logger.info(
                f"Marketing workflow creation request from user {user_id}",
                extra={
                    'request_id': request_id,
                    'user_id': user_id,
                    'team_id': team_id,
                    'project_name': workflow_data.project_name,
                    'target_platforms': [p.value for p in workflow_data.target_platforms],
                    'target_regions': [r.value for r in workflow_data.target_regions],
                    'action': 'marketing_workflow_request'
                }
            )
            
            result = await manager.create_marketing_workflow(
                team_id=team_id,
                project_name=workflow_data.project_name,
                project_description=workflow_data.project_description,
                target_platforms=workflow_data.target_platforms,
                target_regions=workflow_data.target_regions,
                content_types=workflow_data.content_types,
                creator_id=user_id,
                priority=workflow_data.priority
            )
            
            execution_time = time.time() - start_time
            log_api_response(request_id, 200, result, execution_time)
            
            return result
    
    except Exception as e:
        execution_time = time.time() - start_time
        api_logger.error(
            f"Marketing workflow creation failed: {str(e)}",
            extra={
                'request_id': request_id,
                'team_id': team_id,
                'error_type': type(e).__name__,
                'error_message': str(e),
                'execution_time': execution_time,
                'action': 'api_error'
            },
            exc_info=True
        )
        log_api_response(request_id, 500, None, execution_time)
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/teams/{team_id}/analytics", response_model=Dict[str, Any])
async def get_team_analytics(
    request: Request,
    team_id: str,
    manager: BlackboardManager = Depends(get_blackboard_manager)
):
    """Get team analytics and performance metrics"""
    start_time = time.time()
    request_id = log_api_request(request, {"team_id": team_id})
    
    try:
        with performance_logger.time_operation(
            "api_get_team_analytics",
            request_id=request_id,
            team_id=team_id
        ):
            result = await manager.get_team_analytics(team_id)
            
            execution_time = time.time() - start_time
            log_api_response(request_id, 200, result, execution_time)
            
            return result
    
    except Exception as e:
        execution_time = time.time() - start_time
        api_logger.error(
            f"Get team analytics failed: {str(e)}",
            extra={
                'request_id': request_id,
                'team_id': team_id,
                'error_type': type(e).__name__,
                'error_message': str(e),
                'execution_time': execution_time,
                'action': 'api_error'
            },
            exc_info=True
        )
        log_api_response(request_id, 500, None, execution_time)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/teams/{team_id}/workflow-status", response_model=Dict[str, Any])
async def get_team_workflow_status(
    request: Request,
    team_id: str,
    manager: BlackboardManager = Depends(get_blackboard_manager)
):
    """Get comprehensive workflow status for a team"""
    start_time = time.time()
    request_id = log_api_request(request, {"team_id": team_id})
    
    try:
        with performance_logger.time_operation(
            "api_workflow_status",
            request_id=request_id,
            team_id=team_id
        ):
            user_id = request.headers.get('X-User-ID', 'anonymous')
            
            business_logger.logger.info(
                f"Workflow status request from user {user_id}",
                extra={
                    'request_id': request_id,
                    'user_id': user_id,
                    'team_id': team_id,
                    'action': 'workflow_status_request'
                }
            )
            
            from app.core.team_manager import team_manager
            result = await team_manager.get_team_workflow_status(team_id)
            
            execution_time = time.time() - start_time
            log_api_response(request_id, 200, result, execution_time)
            
            return result
            
    except Exception as e:
        execution_time = time.time() - start_time
        error_response = {"status": "error", "error": str(e)}
        log_api_response(request_id, 500, error_response, execution_time)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/teams/{team_id}/workflows/auto-marketing", response_model=Dict[str, Any])
async def create_auto_marketing_workflow(
    request: Request,
    team_id: str,
    workflow_data: CreateMarketingWorkflowRequest,
    manager: BlackboardManager = Depends(get_blackboard_manager)
):
    """Create and auto-start a marketing workflow"""
    start_time = time.time()
    request_id = log_api_request(request, {**workflow_data.model_dump(), "team_id": team_id})
    
    try:
        with performance_logger.time_operation(
            "api_auto_marketing_workflow",
            request_id=request_id,
            team_id=team_id,
            project_name=workflow_data.project_name
        ):
            user_id = request.headers.get('X-User-ID', 'anonymous')
            
            business_logger.logger.info(
                f"Auto marketing workflow creation request from user {user_id}",
                extra={
                    'request_id': request_id,
                    'user_id': user_id,
                    'team_id': team_id,
                    'project_name': workflow_data.project_name,
                    'target_platforms': [p.value for p in workflow_data.target_platforms],
                    'action': 'auto_marketing_workflow_request'
                }
            )
            
            from app.core.team_manager import team_manager
            result = await team_manager.create_auto_marketing_workflow(
                team_id=team_id,
                project_name=workflow_data.project_name,
                project_description=workflow_data.project_description,
                target_platforms=[p.value for p in workflow_data.target_platforms],
                target_regions=[r.value for r in workflow_data.target_regions],
                content_types=[c.value for c in workflow_data.content_types],
                creator_id=user_id
            )
            
            execution_time = time.time() - start_time
            log_api_response(request_id, 200, result, execution_time)
            
            return result
            
    except Exception as e:
        execution_time = time.time() - start_time
        error_response = {"status": "error", "error": str(e)}
        log_api_response(request_id, 500, error_response, execution_time)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/teams/{team_id}/monitoring/dashboard", response_model=Dict[str, Any])
async def get_monitoring_dashboard(
    request: Request,
    team_id: str
):
    """Get real-time monitoring dashboard for a team"""
    start_time = time.time()
    request_id = log_api_request(request, {"team_id": team_id})
    
    try:
        with performance_logger.time_operation(
            "api_monitoring_dashboard",
            request_id=request_id,
            team_id=team_id
        ):
            user_id = request.headers.get('X-User-ID', 'anonymous')
            
            business_logger.logger.info(
                f"Monitoring dashboard request from user {user_id}",
                extra={
                    'request_id': request_id,
                    'user_id': user_id,
                    'team_id': team_id,
                    'action': 'monitoring_dashboard_request'
                }
            )
            
            from app.core.team_manager import team_manager
            monitoring_service = team_manager.get_monitoring_service(team_id)
            
            if not monitoring_service:
                return {
                    "status": "no_monitoring",
                    "message": "Monitoring service not found for this team",
                    "team_id": team_id
                }
            
            result = await monitoring_service.get_monitoring_dashboard()
            
            execution_time = time.time() - start_time
            log_api_response(request_id, 200, result, execution_time)
            
            return result
            
    except Exception as e:
        execution_time = time.time() - start_time
        error_response = {"status": "error", "error": str(e)}
        log_api_response(request_id, 500, error_response, execution_time)
        raise HTTPException(status_code=500, detail=str(e)) 