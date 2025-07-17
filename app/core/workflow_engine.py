import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set, Tuple
from dataclasses import dataclass, field
from enum import Enum
from uuid import uuid4
import json

from app.types.blackboard import (
    BlackboardTask, TaskStatus, TaskPriority, ExpertRole,
    TaskDependency, DependencyType
)
from app.core.blackboard import BlackBoard
from app.clients.redis_client import redis_client_instance
from app.utils.logging import get_business_logger, get_performance_logger


class WorkflowStatus(Enum):
    """工作流状态"""
    CREATED = "created"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class WorkflowTriggerType(Enum):
    """工作流触发类型"""
    MANUAL = "manual"          # 手动触发
    AUTO_SCHEDULE = "auto_schedule"  # 自动调度
    EVENT_DRIVEN = "event_driven"    # 事件驱动
    TIME_BASED = "time_based"       # 时间触发


@dataclass
class WorkflowNode:
    """工作流节点（任务）"""
    task_id: str
    node_name: str
    expert_role: ExpertRole
    dependencies: List[str] = field(default_factory=list)  # 依赖的task_id列表
    status: TaskStatus = TaskStatus.PENDING
    estimated_duration: int = 60  # 预估执行时间（分钟）
    retry_count: int = 0
    max_retries: int = 3
    parallel_group: Optional[str] = None  # 并行组，同组任务可并行执行
    
    def is_ready_to_execute(self, completed_tasks: Set[str]) -> bool:
        """检查节点是否准备好执行"""
        return all(dep_id in completed_tasks for dep_id in self.dependencies)


@dataclass 
class WorkflowDefinition:
    """工作流定义"""
    workflow_id: str
    workflow_name: str
    team_id: str
    nodes: List[WorkflowNode] = field(default_factory=list)
    status: WorkflowStatus = WorkflowStatus.CREATED
    trigger_type: WorkflowTriggerType = WorkflowTriggerType.MANUAL
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    metadata: Dict = field(default_factory=dict)
    
    def get_ready_nodes(self, completed_tasks: Set[str], running_tasks: Set[str]) -> List[WorkflowNode]:
        """获取准备执行的节点"""
        ready_nodes = []
        for node in self.nodes:
            if (node.status == TaskStatus.PENDING and 
                node.task_id not in running_tasks and
                node.is_ready_to_execute(completed_tasks)):
                ready_nodes.append(node)
        return ready_nodes
    
    def get_parallel_groups(self) -> Dict[str, List[WorkflowNode]]:
        """获取并行组"""
        groups = {}
        for node in self.nodes:
            if node.parallel_group:
                if node.parallel_group not in groups:
                    groups[node.parallel_group] = []
                groups[node.parallel_group].append(node)
        return groups


class WorkflowEngine:
    """
    工作流引擎 - 管理任务依赖关系和执行顺序
    
    核心功能：
    1. 定义和管理工作流
    2. 处理任务依赖关系
    3. 自动化工作流执行
    4. 支持并行和串行任务执行
    5. 工作流监控和状态管理
    """
    
    def __init__(self, team_id: str):
        """初始化工作流引擎"""
        self.team_id = team_id
        self.redis_client = redis_client_instance.get_redis_client()
        self.logger = logging.getLogger(f"WorkflowEngine-{team_id}")
        self.business_logger = get_business_logger()
        self.performance_logger = get_performance_logger()
        
        # 运行状态
        self.active_workflows: Dict[str, WorkflowDefinition] = {}
        self.is_running = False
        self.execution_interval = 10  # 10秒检查一次
        
        # Redis键前缀
        self.workflow_prefix = f"workflow:{team_id}"
        self.execution_key = f"workflow_execution:{team_id}"
        
        self.logger.info(f"WorkflowEngine initialized for team {team_id}")
    
    async def start_engine(self):
        """启动工作流引擎"""
        if self.is_running:
            self.logger.warning("WorkflowEngine is already running")
            return
        
        self.is_running = True
        self.logger.info("Starting WorkflowEngine")
        
        # 加载已保存的工作流
        await self._load_workflows()
        
        # 启动执行循环
        asyncio.create_task(self._execution_loop())
        
        await self._log_workflow_event("engine_started", {
            "team_id": self.team_id,
            "active_workflows": len(self.active_workflows)
        })
    
    async def stop_engine(self):
        """停止工作流引擎"""
        self.is_running = False
        self.logger.info("Stopping WorkflowEngine")
        
        # 保存工作流状态
        await self._save_workflows()
        
        await self._log_workflow_event("engine_stopped", {
            "team_id": self.team_id,
            "workflows_saved": len(self.active_workflows)
        })
    
    # === 工作流定义管理 ===
    
    async def create_workflow(
        self,
        workflow_name: str,
        trigger_type: WorkflowTriggerType = WorkflowTriggerType.MANUAL,
        metadata: Dict = None
    ) -> WorkflowDefinition:
        """创建新工作流"""
        
        workflow = WorkflowDefinition(
            workflow_id=str(uuid4()),
            workflow_name=workflow_name,
            team_id=self.team_id,
            trigger_type=trigger_type,
            metadata=metadata or {}
        )
        
        self.active_workflows[workflow.workflow_id] = workflow
        await self._save_workflow(workflow)
        
        self.logger.info(
            f"Created workflow {workflow.workflow_id}: {workflow_name}",
            extra={
                'workflow_id': workflow.workflow_id,
                'workflow_name': workflow_name,
                'team_id': self.team_id,
                'trigger_type': trigger_type.value,
                'action': 'workflow_created'
            }
        )
        
        return workflow
    
    async def add_task_to_workflow(
        self,
        workflow_id: str,
        task_id: str,
        node_name: str,
        expert_role: ExpertRole,
        dependencies: List[str] = None,
        estimated_duration: int = 60,
        parallel_group: str = None
    ) -> bool:
        """向工作流添加任务节点"""
        
        workflow = self.active_workflows.get(workflow_id)
        if not workflow:
            self.logger.error(f"Workflow {workflow_id} not found")
            return False
        
        # 检查任务是否已存在
        existing_node = next((n for n in workflow.nodes if n.task_id == task_id), None)
        if existing_node:
            self.logger.warning(f"Task {task_id} already exists in workflow {workflow_id}")
            return False
        
        # 创建工作流节点
        node = WorkflowNode(
            task_id=task_id,
            node_name=node_name,
            expert_role=expert_role,
            dependencies=dependencies or [],
            estimated_duration=estimated_duration,
            parallel_group=parallel_group
        )
        
        workflow.nodes.append(node)
        await self._save_workflow(workflow)
        
        self.logger.info(
            f"Added task {task_id} to workflow {workflow_id}",
            extra={
                'workflow_id': workflow_id,
                'task_id': task_id,
                'node_name': node_name,
                'dependencies': dependencies or [],
                'team_id': self.team_id,
                'action': 'task_added_to_workflow'
            }
        )
        
        return True
    
    async def create_marketing_workflow(
        self,
        project_name: str,
        project_description: str,
        target_platforms: List = None,
        target_regions: List = None,
        content_types: List = None,
        creator_id: str = "system"
    ) -> WorkflowDefinition:
        """创建营销工作流（Jeff -> Monica -> Henry）"""
        
        # 创建工作流
        workflow = await self.create_workflow(
            workflow_name=f"Marketing: {project_name}",
            trigger_type=WorkflowTriggerType.AUTO_SCHEDULE,
            metadata={
                "project_name": project_name,
                "project_description": project_description,
                "creator_id": creator_id,
                "workflow_type": "marketing"
            }
        )
        
        # 创建任务并添加到BlackBoard
        from app.core.team_manager import team_manager
        
        # 1. Jeff任务 - 策略制定
        planning_task = await team_manager.submit_task(
            team_id=self.team_id,
            title=f"Marketing Strategy: {project_name}",
            description=f"Create comprehensive marketing strategy for {project_description}",
            goal="Develop platform-specific marketing strategy with content calendar and campaign structure",
            required_expert_role=ExpertRole.PLANNER,
            creator_id=creator_id,
            target_platforms=target_platforms or [],
            target_regions=target_regions or [],
            content_types=content_types or [],
            metadata={
                "project_name": project_name,
                "workflow_id": workflow.workflow_id,
                "workflow_type": "marketing"
            }
        )
        
        # 2. Monica任务 - 内容生成
        content_task = await team_manager.submit_task(
            team_id=self.team_id,
            title=f"Content Creation: {project_name}",
            description=f"Generate platform-adapted content based on marketing strategy for {project_description}",
            goal="Create high-quality, platform-optimized content using marketing techniques",
            required_expert_role=ExpertRole.EXECUTOR,
            creator_id=creator_id,
            target_platforms=target_platforms or [],
            target_regions=target_regions or [],
            content_types=content_types or [],
            metadata={
                "project_name": project_name,
                "workflow_id": workflow.workflow_id,
                "workflow_type": "content_generation"
            }
        )
        
        # 3. Henry任务 - 合规审核
        review_task = await team_manager.submit_task(
            team_id=self.team_id,
            title=f"Content Review: {project_name}",
            description=f"Review content for compliance and quality assurance for {project_description}",
            goal="Ensure content meets platform policies and regional compliance requirements",
            required_expert_role=ExpertRole.EVALUATOR,
            creator_id=creator_id,
            target_platforms=target_platforms or [],
            target_regions=target_regions or [],
            content_types=content_types or [],
            metadata={
                "project_name": project_name,
                "workflow_id": workflow.workflow_id,
                "workflow_type": "compliance_review"
            }
        )
        
        # 将任务添加到工作流，设置依赖关系
        if planning_task:
            await self.add_task_to_workflow(
                workflow.workflow_id,
                planning_task.task_id,
                "Marketing Strategy Planning",
                ExpertRole.PLANNER,
                dependencies=[],  # 第一个任务，无依赖
                estimated_duration=120  # 2小时
            )
        
        if content_task and planning_task:
            await self.add_task_to_workflow(
                workflow.workflow_id,
                content_task.task_id,
                "Content Generation",
                ExpertRole.EXECUTOR,
                dependencies=[planning_task.task_id],  # 依赖策略任务
                estimated_duration=180  # 3小时
            )
        
        if review_task and content_task:
            await self.add_task_to_workflow(
                workflow.workflow_id,
                review_task.task_id,
                "Content Review & Compliance",
                ExpertRole.EVALUATOR,
                dependencies=[content_task.task_id],  # 依赖内容生成任务
                estimated_duration=90  # 1.5小时
            )
        
        self.logger.info(
            f"Created marketing workflow {workflow.workflow_id} with {len(workflow.nodes)} tasks",
            extra={
                'workflow_id': workflow.workflow_id,
                'project_name': project_name,
                'team_id': self.team_id,
                'task_count': len(workflow.nodes),
                'action': 'marketing_workflow_created'
            }
        )
        
        return workflow
    
    # === 工作流执行管理 ===
    
    async def start_workflow(self, workflow_id: str) -> bool:
        """启动工作流执行"""
        
        workflow = self.active_workflows.get(workflow_id)
        if not workflow:
            self.logger.error(f"Workflow {workflow_id} not found")
            return False
        
        if workflow.status != WorkflowStatus.CREATED:
            self.logger.warning(f"Workflow {workflow_id} is not in CREATED status")
            return False
        
        workflow.status = WorkflowStatus.RUNNING
        workflow.started_at = datetime.now()
        await self._save_workflow(workflow)
        
        self.logger.info(
            f"Started workflow {workflow_id}: {workflow.workflow_name}",
            extra={
                'workflow_id': workflow_id,
                'workflow_name': workflow.workflow_name,
                'team_id': self.team_id,
                'node_count': len(workflow.nodes),
                'action': 'workflow_started'
            }
        )
        
        await self._log_workflow_event("workflow_started", {
            "workflow_id": workflow_id,
            "workflow_name": workflow.workflow_name,
            "node_count": len(workflow.nodes)
        })
        
        return True
    
    async def _execution_loop(self):
        """工作流执行循环"""
        while self.is_running:
            try:
                start_time = datetime.now()
                
                # 检查并执行所有活跃工作流
                await self._process_active_workflows()
                
                execution_time = (datetime.now() - start_time).total_seconds()
                if execution_time > 5:  # 如果执行时间超过5秒，记录警告
                    self.logger.warning(f"Workflow execution took {execution_time:.2f}s")
                
                await asyncio.sleep(self.execution_interval)
                
            except Exception as e:
                self.logger.error(f"Error in workflow execution loop: {str(e)}", exc_info=True)
                await asyncio.sleep(self.execution_interval)
    
    async def _process_active_workflows(self):
        """处理所有活跃的工作流"""
        
        running_workflows = [
            wf for wf in self.active_workflows.values()
            if wf.status == WorkflowStatus.RUNNING
        ]
        
        if not running_workflows:
            return
        
        self.logger.debug(f"Processing {len(running_workflows)} active workflows")
        
        for workflow in running_workflows:
            try:
                await self._process_workflow(workflow)
            except Exception as e:
                self.logger.error(
                    f"Error processing workflow {workflow.workflow_id}: {str(e)}",
                    exc_info=True
                )
                # 标记工作流为失败
                workflow.status = WorkflowStatus.FAILED
                await self._save_workflow(workflow)
    
    async def _process_workflow(self, workflow: WorkflowDefinition):
        """处理单个工作流"""
        
        # 获取当前任务状态
        completed_tasks, running_tasks, failed_tasks = await self._get_workflow_task_status(workflow)
        
        # 检查工作流是否完成
        if len(completed_tasks) == len(workflow.nodes):
            workflow.status = WorkflowStatus.COMPLETED
            workflow.completed_at = datetime.now()
            await self._save_workflow(workflow)
            
            self.logger.info(
                f"Workflow {workflow.workflow_id} completed successfully",
                extra={
                    'workflow_id': workflow.workflow_id,
                    'workflow_name': workflow.workflow_name,
                    'team_id': self.team_id,
                    'duration': (workflow.completed_at - workflow.started_at).total_seconds(),
                    'action': 'workflow_completed'
                }
            )
            
            await self._log_workflow_event("workflow_completed", {
                "workflow_id": workflow.workflow_id,
                "workflow_name": workflow.workflow_name,
                "completed_tasks": len(completed_tasks),
                "total_tasks": len(workflow.nodes)
            })
            return
        
        # 检查是否有失败的任务需要重试
        await self._handle_failed_tasks(workflow, failed_tasks)
        
        # 获取准备执行的任务节点
        ready_nodes = workflow.get_ready_nodes(completed_tasks, running_tasks)
        
        if ready_nodes:
            self.logger.debug(
                f"Found {len(ready_nodes)} ready nodes in workflow {workflow.workflow_id}"
            )
            
            # 执行准备好的任务
            for node in ready_nodes:
                await self._execute_workflow_node(workflow, node)
    
    async def _get_workflow_task_status(
        self, 
        workflow: WorkflowDefinition
    ) -> Tuple[Set[str], Set[str], Set[str]]:
        """获取工作流中任务的状态"""
        
        from app.core.team_manager import team_manager
        
        blackboard = team_manager.get_blackboard(self.team_id)
        if not blackboard:
            return set(), set(), set()
        
        completed_tasks = set()
        running_tasks = set()
        failed_tasks = set()
        
        for node in workflow.nodes:
            task = await blackboard.get_task(node.task_id)
            if task:
                if task.status == TaskStatus.COMPLETED:
                    completed_tasks.add(node.task_id)
                    node.status = TaskStatus.COMPLETED
                elif task.status in [TaskStatus.ASSIGNED, TaskStatus.IN_PROGRESS]:
                    running_tasks.add(node.task_id)
                    node.status = task.status
                elif task.status == TaskStatus.FAILED:
                    failed_tasks.add(node.task_id)
                    node.status = TaskStatus.FAILED
        
        return completed_tasks, running_tasks, failed_tasks
    
    async def _handle_failed_tasks(self, workflow: WorkflowDefinition, failed_tasks: Set[str]):
        """处理失败的任务"""
        
        for task_id in failed_tasks:
            node = next((n for n in workflow.nodes if n.task_id == task_id), None)
            if not node:
                continue
            
            if node.retry_count < node.max_retries:
                self.logger.info(
                    f"Retrying failed task {task_id} (attempt {node.retry_count + 1}/{node.max_retries})"
                )
                
                # 重置任务状态
                from app.core.team_manager import team_manager
                blackboard = team_manager.get_blackboard(self.team_id)
                if blackboard:
                    task = await blackboard.get_task(task_id)
                    if task:
                        task.status = TaskStatus.PENDING
                        await blackboard._store_task(task)
                        node.retry_count += 1
                        node.status = TaskStatus.PENDING
            else:
                self.logger.error(
                    f"Task {task_id} failed after {node.max_retries} retries, marking workflow as failed"
                )
                workflow.status = WorkflowStatus.FAILED
                await self._save_workflow(workflow)
    
    async def _execute_workflow_node(self, workflow: WorkflowDefinition, node: WorkflowNode):
        """执行工作流节点（触发任务执行）"""
        
        from app.core.team_manager import team_manager
        
        self.logger.info(
            f"Triggering execution of task {node.task_id} in workflow {workflow.workflow_id}",
            extra={
                'workflow_id': workflow.workflow_id,
                'task_id': node.task_id,
                'node_name': node.node_name,
                'team_id': self.team_id,
                'action': 'workflow_task_triggered'
            }
        )
        
        # 触发任务执行（异步）
        asyncio.create_task(
            self._execute_task_async(node.task_id)
        )
    
    async def _execute_task_async(self, task_id: str):
        """异步执行任务"""
        try:
            from app.core.team_manager import team_manager
            
            result = await team_manager.execute_task(self.team_id, task_id)
            
            self.logger.info(
                f"Task {task_id} execution result: {result.get('status', 'unknown')}",
                extra={
                    'task_id': task_id,
                    'team_id': self.team_id,
                    'result_status': result.get('status', 'unknown'),
                    'action': 'workflow_task_executed'
                }
            )
            
        except Exception as e:
            self.logger.error(
                f"Error executing task {task_id}: {str(e)}",
                extra={
                    'task_id': task_id,
                    'team_id': self.team_id,
                    'error': str(e),
                    'action': 'workflow_task_execution_error'
                }
            )
    
    # === 持久化管理 ===
    
    async def _save_workflow(self, workflow: WorkflowDefinition):
        """保存工作流到Redis"""
        workflow_key = f"{self.workflow_prefix}:{workflow.workflow_id}"
        workflow_data = {
            "workflow_id": workflow.workflow_id,
            "workflow_name": workflow.workflow_name,
            "team_id": workflow.team_id,
            "status": workflow.status.value,
            "trigger_type": workflow.trigger_type.value,
            "created_at": workflow.created_at.isoformat(),
            "started_at": workflow.started_at.isoformat() if workflow.started_at else None,
            "completed_at": workflow.completed_at.isoformat() if workflow.completed_at else None,
            "metadata": workflow.metadata,
            "nodes": [
                {
                    "task_id": node.task_id,
                    "node_name": node.node_name,
                    "expert_role": node.expert_role.value,
                    "dependencies": node.dependencies,
                    "status": node.status.value,
                    "estimated_duration": node.estimated_duration,
                    "retry_count": node.retry_count,
                    "max_retries": node.max_retries,
                    "parallel_group": node.parallel_group
                }
                for node in workflow.nodes
            ]
        }
        
        await self._set_redis_value(workflow_key, workflow_data)
    
    async def _load_workflows(self):
        """从Redis加载工作流"""
        try:
            # 获取所有工作流键
            pattern = f"{self.workflow_prefix}:*"
            keys = await self.redis_client.keys(pattern)
            
            for key in keys:
                workflow_data = await self._get_redis_value(key)
                if workflow_data:
                    workflow = await self._deserialize_workflow(workflow_data)
                    if workflow:
                        self.active_workflows[workflow.workflow_id] = workflow
            
            self.logger.info(f"Loaded {len(self.active_workflows)} workflows from Redis")
            
        except Exception as e:
            self.logger.error(f"Error loading workflows: {str(e)}")
    
    async def _save_workflows(self):
        """保存所有工作流到Redis"""
        for workflow in self.active_workflows.values():
            await self._save_workflow(workflow)
    
    async def _deserialize_workflow(self, data: Dict) -> Optional[WorkflowDefinition]:
        """反序列化工作流数据"""
        try:
            workflow = WorkflowDefinition(
                workflow_id=data["workflow_id"],
                workflow_name=data["workflow_name"],
                team_id=data["team_id"],
                status=WorkflowStatus(data["status"]),
                trigger_type=WorkflowTriggerType(data["trigger_type"]),
                created_at=datetime.fromisoformat(data["created_at"]),
                started_at=datetime.fromisoformat(data["started_at"]) if data.get("started_at") else None,
                completed_at=datetime.fromisoformat(data["completed_at"]) if data.get("completed_at") else None,
                metadata=data.get("metadata", {})
            )
            
            # 反序列化节点
            for node_data in data.get("nodes", []):
                node = WorkflowNode(
                    task_id=node_data["task_id"],
                    node_name=node_data["node_name"],
                    expert_role=ExpertRole(node_data["expert_role"]),
                    dependencies=node_data.get("dependencies", []),
                    status=TaskStatus(node_data.get("status", "pending")),
                    estimated_duration=node_data.get("estimated_duration", 60),
                    retry_count=node_data.get("retry_count", 0),
                    max_retries=node_data.get("max_retries", 3),
                    parallel_group=node_data.get("parallel_group")
                )
                workflow.nodes.append(node)
            
            return workflow
            
        except Exception as e:
            self.logger.error(f"Error deserializing workflow: {str(e)}")
            return None
    
    # === 公共接口 ===
    
    async def get_workflow_status(self, workflow_id: str) -> Optional[Dict]:
        """获取工作流状态"""
        workflow = self.active_workflows.get(workflow_id)
        if not workflow:
            return None
        
        completed_tasks, running_tasks, failed_tasks = await self._get_workflow_task_status(workflow)
        
        return {
            "workflow_id": workflow.workflow_id,
            "workflow_name": workflow.workflow_name,
            "status": workflow.status.value,
            "progress": {
                "total_tasks": len(workflow.nodes),
                "completed_tasks": len(completed_tasks),
                "running_tasks": len(running_tasks),
                "failed_tasks": len(failed_tasks),
                "completion_percentage": len(completed_tasks) / len(workflow.nodes) * 100 if workflow.nodes else 0
            },
            "timing": {
                "created_at": workflow.created_at.isoformat(),
                "started_at": workflow.started_at.isoformat() if workflow.started_at else None,
                "completed_at": workflow.completed_at.isoformat() if workflow.completed_at else None,
                "estimated_remaining": self._estimate_remaining_time(workflow, completed_tasks, running_tasks)
            },
            "nodes": [
                {
                    "task_id": node.task_id,
                    "node_name": node.node_name,
                    "status": node.status.value,
                    "dependencies": node.dependencies,
                    "retry_count": node.retry_count
                }
                for node in workflow.nodes
            ]
        }
    
    def _estimate_remaining_time(
        self, 
        workflow: WorkflowDefinition, 
        completed_tasks: Set[str], 
        running_tasks: Set[str]
    ) -> int:
        """估算剩余执行时间（分钟）"""
        remaining_time = 0
        
        for node in workflow.nodes:
            if node.task_id not in completed_tasks and node.task_id not in running_tasks:
                remaining_time += node.estimated_duration
        
        return remaining_time
    
    async def list_workflows(self) -> List[Dict]:
        """列出所有工作流"""
        workflows = []
        for workflow in self.active_workflows.values():
            status = await self.get_workflow_status(workflow.workflow_id)
            if status:
                workflows.append(status)
        
        return workflows
    
    async def _log_workflow_event(self, event_type: str, data: Dict):
        """记录工作流事件"""
        self.business_logger.logger.info(
            f"Workflow event: {event_type}",
            extra={
                'team_id': self.team_id,
                'event_type': event_type,
                'event_data': data,
                'action': 'workflow_event'
            }
        )
    
    # === Redis辅助方法 ===
    
    async def _set_redis_value(self, key: str, value):
        """设置Redis值"""
        try:
            await self.redis_client.set(key, json.dumps(value, default=str))
        except Exception as e:
            self.logger.error(f"Redis set error: {str(e)}")
    
    async def _get_redis_value(self, key: str):
        """获取Redis值"""
        try:
            value = await self.redis_client.get(key)
            if value:
                return json.loads(value)
            return None
        except Exception as e:
            self.logger.error(f"Redis get error: {str(e)}")
            return None 