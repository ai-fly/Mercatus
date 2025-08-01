import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set
from dataclasses import dataclass, field
from enum import Enum
from uuid import uuid4
import json

from app.core.auto_scheduler import AutoTaskScheduler
from app.core.workflow_engine import WorkflowEngine, WorkflowStatus
from app.core.dependency_manager import TaskDependencyManager
from app.types.blackboard import TaskStatus, TaskPriority, ExpertRole
from app.clients.redis_client import redis_client_instance
from app.utils.logging import get_business_logger, get_performance_logger


class MonitoringMode(Enum):
    """监控模式"""
    PASSIVE = "passive"         # 被动监控，只记录状态
    ACTIVE = "active"           # 主动监控，自动执行任务
    INTELLIGENT = "intelligent" # 智能监控，基于机器学习优化


@dataclass
class MonitoringMetrics:
    """监控指标"""
    total_tasks_processed: int = 0
    tasks_auto_executed: int = 0
    tasks_failed: int = 0
    tasks_retried: int = 0
    average_execution_time: float = 0.0
    system_utilization: float = 0.0
    workflow_completion_rate: float = 0.0
    last_update: datetime = field(default_factory=datetime.now)
    
    def update_execution_time(self, execution_time: float):
        """更新平均执行时间"""
        if self.tasks_auto_executed == 0:
            self.average_execution_time = execution_time
        else:
            self.average_execution_time = (
                (self.average_execution_time * self.tasks_auto_executed + execution_time) /
                (self.tasks_auto_executed + 1)
            )
        self.tasks_auto_executed += 1
        self.total_tasks_processed += 1
        self.last_update = datetime.now()


@dataclass
class MonitoringAlert:
    """监控告警"""
    alert_id: str
    alert_type: str
    severity: str  # low, medium, high, critical
    message: str
    details: Dict
    created_at: datetime = field(default_factory=datetime.now)
    resolved_at: Optional[datetime] = None
    is_resolved: bool = False


class ContinuousMonitoringService:
    """
    持续监控服务 - 后台持续监控和自动执行任务
    
    核心功能：
    1. 整合自动调度器、工作流引擎和依赖管理器
    2. 持续监控系统状态和任务进度
    3. 自动触发任务执行
    4. 异常检测和告警
    5. 性能优化和自动调整
    6. 提供实时监控Dashboard
    """
    
    def __init__(self, team_id: str):
        """初始化持续监控服务"""
        self.team_id = team_id
        self.redis_client = redis_client_instance.get_redis_client()
        self.logger = logging.getLogger(f"ContinuousMonitor-{team_id}")
        self.business_logger = get_business_logger()
        self.performance_logger = get_performance_logger()
        
        # 核心组件
        self.scheduler = AutoTaskScheduler(team_id)
        self.workflow_engine = WorkflowEngine(team_id)
        self.dependency_manager = TaskDependencyManager(team_id)
        
        # 监控状态
        self.is_running = False
        self.monitoring_mode = MonitoringMode.ACTIVE
        self.monitoring_interval = 15  # 15秒检查一次
        
        # 监控指标
        self.metrics = MonitoringMetrics()
        self.alerts: Dict[str, MonitoringAlert] = {}
        
        # 配置参数
        self.config = {
            "max_concurrent_executions": 5,
            "task_timeout_minutes": 30,
            "retry_failed_tasks": True,
            "auto_scale_experts": True,
            "alert_thresholds": {
                "high_failure_rate": 0.3,
                "low_completion_rate": 0.5,
                "high_response_time": 300  # 5分钟
            }
        }
        
        # Redis键
        self.monitor_key = f"monitor:{team_id}"
        self.metrics_key = f"monitor_metrics:{team_id}"
        self.alerts_key = f"monitor_alerts:{team_id}"
        
        self.logger.info(f"ContinuousMonitoringService initialized for team {team_id}")
    
    async def start_monitoring(self):
        """启动持续监控服务"""
        if self.is_running:
            self.logger.warning("Monitoring service is already running")
            return
        
        self.is_running = True
        self.logger.info("Starting ContinuousMonitoringService")
        
        # 初始化各个组件
        await self._initialize_components()
        
        # 启动监控循环
        asyncio.create_task(self._monitoring_loop())
        
        # 启动告警处理
        asyncio.create_task(self._alert_handler_loop())
        
        await self._log_monitor_event("monitoring_started", {
            "team_id": self.team_id,
            "monitoring_mode": self.monitoring_mode.value,
            "monitoring_interval": self.monitoring_interval
        })
    
    async def stop_monitoring(self):
        """停止持续监控服务"""
        self.is_running = False
        self.logger.info("Stopping ContinuousMonitoringService")
        
        # 停止各个组件
        await self.scheduler.stop_scheduler()
        await self.workflow_engine.stop_engine()
        
        # 保存最终指标
        await self._save_metrics()
        
        await self._log_monitor_event("monitoring_stopped", {
            "team_id": self.team_id,
            "final_metrics": self.metrics.__dict__
        })
    
    async def _initialize_components(self):
        """初始化各个组件"""
        try:
            # 初始化依赖管理器
            await self.dependency_manager.initialize()
            
            # 启动调度器
            await self.scheduler.start_scheduler()
            
            # 启动工作流引擎
            await self.workflow_engine.start_engine()
            
            self.logger.info("All monitoring components initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Error initializing components: {str(e)}", exc_info=True)
            raise
    
    async def _monitoring_loop(self):
        """主监控循环"""
        while self.is_running:
            try:
                start_time = datetime.now()
                
                # 执行监控检查
                await self._run_monitoring_cycle()
                
                # 更新系统指标
                execution_time = (datetime.now() - start_time).total_seconds()
                await self._update_system_metrics(execution_time)
                
                # 检查告警条件
                await self._check_alert_conditions()
                
                # 等待下一轮
                await asyncio.sleep(self.monitoring_interval)
                
            except Exception as e:
                self.logger.error(f"Error in monitoring loop: {str(e)}", exc_info=True)
                await asyncio.sleep(self.monitoring_interval)
    
    async def _run_monitoring_cycle(self):
        """执行一轮监控检查"""
        
        with self.performance_logger.time_operation(
            "monitoring_cycle",
            team_id=self.team_id
        ):
            
            # 1. 检查工作流状态
            await self._monitor_workflows()
            
            # 2. 检查任务依赖
            await self._monitor_task_dependencies()
            
            # 3. 触发任务执行
            if self.monitoring_mode in [MonitoringMode.ACTIVE, MonitoringMode.INTELLIGENT]:
                await self._trigger_task_executions()
            
            # 4. 检查超时任务
            await self._check_timeout_tasks()
            
            # 5. 处理失败任务
            await self._handle_failed_tasks()
            
            # 6. 优化系统性能
            if self.monitoring_mode == MonitoringMode.INTELLIGENT:
                await self._optimize_system_performance()
    
    async def _monitor_workflows(self):
        """监控工作流状态"""
        
        workflows = await self.workflow_engine.list_workflows()
        
        for workflow in workflows:
            workflow_id = workflow["workflow_id"]
            status = workflow["status"]
            progress = workflow["progress"]
            
            # 检查卡住的工作流
            if (status == "running" and 
                progress["running_tasks"] == 0 and 
                progress["completed_tasks"] < progress["total_tasks"]):
                
                await self._create_alert(
                    "workflow_stuck",
                    "medium",
                    f"Workflow {workflow_id} appears to be stuck",
                    {
                        "workflow_id": workflow_id,
                        "progress": progress,
                        "suggestion": "Check task dependencies or restart workflow"
                    }
                )
            
            # 检查高失败率工作流
            if progress["failed_tasks"] > 0:
                failure_rate = progress["failed_tasks"] / progress["total_tasks"]
                if failure_rate > self.config["alert_thresholds"]["high_failure_rate"]:
                    await self._create_alert(
                        "high_failure_rate",
                        "high",
                        f"Workflow {workflow_id} has high failure rate: {failure_rate:.1%}",
                        {
                            "workflow_id": workflow_id,
                            "failure_rate": failure_rate,
                            "failed_tasks": progress["failed_tasks"],
                            "total_tasks": progress["total_tasks"]
                        }
                    )
    
    async def _monitor_task_dependencies(self):
        """监控任务依赖状态"""
        
        dependency_status = await self.dependency_manager.get_dependency_status()
        ready_tasks = dependency_status["ready_tasks"]
        
        # 检查准备好但未执行的任务
        from app.core.team_manager import team_manager
        blackboard = team_manager.get_blackboard(self.team_id)
        
        if blackboard:
            stuck_tasks = []
            for task_id in ready_tasks:
                task = await blackboard.get_task(task_id)
                if task and task.status == TaskStatus.PENDING:
                    # 检查任务等待时间
                    waiting_time = (datetime.now() - task.created_at).total_seconds() / 60
                    if waiting_time > 10:  # 等待超过10分钟
                        stuck_tasks.append((task_id, waiting_time))
            
            if stuck_tasks:
                await self._create_alert(
                    "tasks_waiting_too_long",
                    "medium",
                    f"{len(stuck_tasks)} tasks have been waiting for execution",
                    {
                        "stuck_tasks": [
                            {"task_id": task_id, "waiting_minutes": waiting_time}
                            for task_id, waiting_time in stuck_tasks
                        ]
                    }
                )
    
    async def _trigger_task_executions(self):
        """触发任务执行"""
        
        # 获取准备好的任务
        ready_tasks = await self.dependency_manager.get_ready_tasks()
        
        if not ready_tasks:
            return
        
        # 获取当前正在执行的任务数量
        from app.core.team_manager import team_manager
        blackboard = team_manager.get_blackboard(self.team_id)
        
        if not blackboard:
            return
        
        # 统计正在执行的任务
        running_count = 0
        for task_id in ready_tasks:
            task = await blackboard.get_task(task_id)
            if task and task.status in [TaskStatus.ASSIGNED, TaskStatus.IN_PROGRESS]:
                running_count += 1
        
        # 检查并发限制
        available_slots = self.config["max_concurrent_executions"] - running_count
        
        if available_slots <= 0:
            self.logger.debug("Max concurrent executions reached, skipping task trigger")
            return
        
        # 执行准备好的任务（按优先级排序）
        tasks_to_execute = []
        for task_id in ready_tasks:
            task = await blackboard.get_task(task_id)
            if task and task.status == TaskStatus.PENDING:
                tasks_to_execute.append(task)
        
        # 按优先级排序
        tasks_to_execute.sort(
            key=lambda t: (
                {"urgent": 4, "high": 3, "medium": 2, "low": 1}.get(t.priority.value, 0),
                -t.created_at.timestamp()
            ),
            reverse=True
        )
        
        # 执行任务
        executed_count = 0
        for task in tasks_to_execute[:available_slots]:
            try:
                self.logger.info(
                    f"Auto-triggering execution of task {task.task_id}",
                    extra={
                        'task_id': task.task_id,
                        'task_title': task.title,
                        'team_id': self.team_id,
                        'action': 'auto_execution_triggered'
                    }
                )
                
                # 异步执行任务
                asyncio.create_task(self._execute_task_monitored(task.task_id))
                executed_count += 1
                
            except Exception as e:
                self.logger.error(f"Error triggering task {task.task_id}: {str(e)}")
        
        if executed_count > 0:
            self.logger.info(f"Triggered execution of {executed_count} tasks")
    
    async def _execute_task_monitored(self, task_id: str):
        """监控式执行任务"""
        start_time = datetime.now()
        
        try:
            from app.core.team_manager import team_manager
            
            result = await team_manager.execute_task(self.team_id, task_id)
            
            execution_time = (datetime.now() - start_time).total_seconds()
            self.metrics.update_execution_time(execution_time)
            
            if result.get("status") == "completed":
                self.logger.info(
                    f"Task {task_id} completed successfully in {execution_time:.1f}s",
                    extra={
                        'task_id': task_id,
                        'execution_time': execution_time,
                        'team_id': self.team_id,
                        'action': 'auto_execution_completed'
                    }
                )
            else:
                self.metrics.tasks_failed += 1
                await self._create_alert(
                    "task_execution_failed",
                    "medium",
                    f"Task {task_id} execution failed",
                    {
                        "task_id": task_id,
                        "error": result.get("message", "Unknown error"),
                        "execution_time": execution_time
                    }
                )
            
        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            self.metrics.tasks_failed += 1
            
            self.logger.error(
                f"Error executing task {task_id}: {str(e)}",
                extra={
                    'task_id': task_id,
                    'execution_time': execution_time,
                    'team_id': self.team_id,
                    'error': str(e),
                    'action': 'auto_execution_error'
                }
            )
            
            await self._create_alert(
                "task_execution_error",
                "high",
                f"Task {task_id} execution error: {str(e)}",
                {
                    "task_id": task_id,
                    "error": str(e),
                    "execution_time": execution_time
                }
            )
    
    async def _check_timeout_tasks(self):
        """检查超时任务"""
        
        from app.core.team_manager import team_manager
        blackboard = team_manager.get_blackboard(self.team_id)
        
        if not blackboard:
            return
        
        # 获取正在执行的任务
        state = await blackboard.get_blackboard_state()
        in_progress_tasks = state.task_status.get(TaskStatus.IN_PROGRESS, [])
        
        timeout_threshold = timedelta(minutes=self.config["task_timeout_minutes"])
        current_time = datetime.now()
        
        for task_id in in_progress_tasks:
            task = await blackboard.get_task(task_id)
            if task and task.assignment and task.assignment.started_at:
                execution_time = current_time - task.assignment.started_at
                
                if execution_time > timeout_threshold:
                    await self._create_alert(
                        "task_timeout",
                        "high",
                        f"Task {task_id} has been running for {execution_time.total_seconds()/60:.1f} minutes",
                        {
                            "task_id": task_id,
                            "task_title": task.title,
                            "execution_time_minutes": execution_time.total_seconds() / 60,
                            "timeout_threshold_minutes": self.config["task_timeout_minutes"],
                            "expert_instance_id": task.assignment.expert_instance_id
                        }
                    )
    
    async def _handle_failed_tasks(self):
        """处理失败任务"""
        
        if not self.config["retry_failed_tasks"]:
            return
        
        from app.core.team_manager import team_manager
        blackboard = team_manager.get_blackboard(self.team_id)
        
        if not blackboard:
            return
        
        # 获取失败的任务
        state = await blackboard.get_blackboard_state()
        failed_tasks = state.task_status.get(TaskStatus.FAILED, [])
        
        for task_id in failed_tasks:
            task = await blackboard.get_task(task_id)
            if task:
                # 检查重试次数
                retry_count = task.task_metadata.context_data.get('retry_count', 0)
                max_retries = task.task_metadata.context_data.get('max_retries', 3)
                
                if retry_count < max_retries:
                    # 重置任务状态并重试
                    task.status = TaskStatus.PENDING
                    task.task_metadata.context_data['retry_count'] = retry_count + 1
                    await blackboard._store_task(task)
                    
                    self.metrics.tasks_retried += 1
                    
                    self.logger.info(
                        f"Retrying failed task {task_id} (attempt {retry_count + 1}/{max_retries})",
                        extra={
                            'task_id': task_id,
                            'retry_count': retry_count + 1,
                            'max_retries': max_retries,
                            'team_id': self.team_id,
                            'action': 'task_retry'
                        }
                    )
    
    async def _optimize_system_performance(self):
        """智能优化系统性能"""
        
        # 自动调整专家实例
        if self.config["auto_scale_experts"]:
            await self._auto_scale_experts()
        
        # 调整调度参数
        await self._optimize_scheduling_parameters()
    
    async def _auto_scale_experts(self):
        """自动扩缩容专家实例"""
        
        from app.core.team_manager import team_manager
        
        try:
            scaling_result = await team_manager.auto_scale_team(self.team_id)
            
            if scaling_result["actions"]:
                self.logger.info(
                    f"Auto-scaling completed: {len(scaling_result['actions'])} actions",
                    extra={
                        'team_id': self.team_id,
                        'scaling_actions': scaling_result["actions"],
                        'action': 'auto_scaling_completed'
                    }
                )
        
        except Exception as e:
            self.logger.error(f"Error in auto-scaling: {str(e)}")
    
    async def _optimize_scheduling_parameters(self):
        """优化调度参数"""
        
        # 基于当前性能调整调度间隔
        if self.metrics.average_execution_time > 0:
            if self.metrics.average_execution_time > 300:  # 5分钟
                # 执行时间长，降低调度频率
                self.scheduler.scheduling_interval = min(60, self.scheduler.scheduling_interval + 5)
            elif self.metrics.average_execution_time < 60:  # 1分钟
                # 执行时间短，提高调度频率
                self.scheduler.scheduling_interval = max(10, self.scheduler.scheduling_interval - 5)
    
    async def _check_alert_conditions(self):
        """检查告警条件"""
        
        current_time = datetime.now()
        
        # 检查完成率
        if self.metrics.total_tasks_processed > 0:
            completion_rate = (self.metrics.tasks_auto_executed - self.metrics.tasks_failed) / self.metrics.total_tasks_processed
            
            if completion_rate < self.config["alert_thresholds"]["low_completion_rate"]:
                await self._create_alert(
                    "low_completion_rate",
                    "high",
                    f"Low task completion rate: {completion_rate:.1%}",
                    {
                        "completion_rate": completion_rate,
                        "total_processed": self.metrics.total_tasks_processed,
                        "successful": self.metrics.tasks_auto_executed - self.metrics.tasks_failed,
                        "failed": self.metrics.tasks_failed
                    }
                )
        
        # 检查响应时间
        if self.metrics.average_execution_time > self.config["alert_thresholds"]["high_response_time"]:
            await self._create_alert(
                "high_response_time",
                "medium",
                f"High average response time: {self.metrics.average_execution_time:.1f}s",
                {
                    "average_execution_time": self.metrics.average_execution_time,
                    "threshold": self.config["alert_thresholds"]["high_response_time"]
                }
            )
    
    async def _create_alert(self, alert_type: str, severity: str, message: str, details: Dict):
        """创建告警"""
        
        alert = MonitoringAlert(
            alert_id=str(uuid4()),
            alert_type=alert_type,
            severity=severity,
            message=message,
            details=details
        )
        
        self.alerts[alert.alert_id] = alert
        await self._save_alert(alert)
        
        self.logger.warning(
            f"Alert created: {alert_type} - {message}",
            extra={
                'alert_id': alert.alert_id,
                'alert_type': alert_type,
                'severity': severity,
                'team_id': self.team_id,
                'details': details,
                'action': 'alert_created'
            }
        )
    
    async def _alert_handler_loop(self):
        """告警处理循环"""
        while self.is_running:
            try:
                # 处理未解决的告警
                await self._process_alerts()
                
                # 清理过期告警
                await self._cleanup_expired_alerts()
                
                await asyncio.sleep(60)  # 每分钟检查一次
                
            except Exception as e:
                self.logger.error(f"Error in alert handler: {str(e)}", exc_info=True)
                await asyncio.sleep(60)
    
    async def _process_alerts(self):
        """处理告警"""
        
        unresolved_alerts = [alert for alert in self.alerts.values() if not alert.is_resolved]
        
        for alert in unresolved_alerts:
            # 自动解决某些类型的告警
            if alert.alert_type == "tasks_waiting_too_long":
                # 强制执行一轮调度
                await self.scheduler.force_scheduling_round()
                await self._resolve_alert(alert.alert_id)
            
            elif alert.alert_type == "workflow_stuck":
                # 尝试重启工作流
                workflow_id = alert.details.get("workflow_id")
                if workflow_id:
                    workflow = self.workflow_engine.active_workflows.get(workflow_id)
                    if workflow:
                        workflow.status = WorkflowStatus.RUNNING
                        await self.workflow_engine._save_workflow(workflow)
                        await self._resolve_alert(alert.alert_id)
    
    async def _resolve_alert(self, alert_id: str):
        """解决告警"""
        
        if alert_id in self.alerts:
            alert = self.alerts[alert_id]
            alert.is_resolved = True
            alert.resolved_at = datetime.now()
            
            await self._save_alert(alert)
            
            self.logger.info(
                f"Alert resolved: {alert.alert_type}",
                extra={
                    'alert_id': alert_id,
                    'alert_type': alert.alert_type,
                    'team_id': self.team_id,
                    'action': 'alert_resolved'
                }
            )
    
    async def _cleanup_expired_alerts(self):
        """清理过期告警"""
        
        current_time = datetime.now()
        expired_threshold = timedelta(hours=24)  # 24小时后清理
        
        expired_alerts = []
        for alert_id, alert in self.alerts.items():
            if alert.is_resolved and (current_time - alert.resolved_at) > expired_threshold:
                expired_alerts.append(alert_id)
        
        for alert_id in expired_alerts:
            del self.alerts[alert_id]
            # 从Redis删除
            await self._delete_alert(alert_id)
    
    async def _update_system_metrics(self, execution_time: float):
        """更新系统指标"""
        
        # 计算系统利用率
        from app.core.team_manager import team_manager
        team = await team_manager.get_team(self.team_id)
        
        if team:
            total_capacity = sum(expert.max_concurrent_tasks for expert in team.expert_instances)
            current_load = sum(expert.current_task_count for expert in team.expert_instances)
            
            self.metrics.system_utilization = current_load / total_capacity if total_capacity > 0 else 0
        
        # 计算工作流完成率
        workflows = await self.workflow_engine.list_workflows()
        if workflows:
            completed_workflows = len([wf for wf in workflows if wf["status"] == "completed"])
            self.metrics.workflow_completion_rate = completed_workflows / len(workflows)
        
        self.metrics.last_update = datetime.now()
        
        # 保存指标
        await self._save_metrics()
    
    # === 持久化管理 ===
    
    async def _save_metrics(self):
        """保存监控指标"""
        metrics_data = {
            "team_id": self.team_id,
            "timestamp": datetime.now().isoformat(),
            "metrics": {
                "total_tasks_processed": self.metrics.total_tasks_processed,
                "tasks_auto_executed": self.metrics.tasks_auto_executed,
                "tasks_failed": self.metrics.tasks_failed,
                "tasks_retried": self.metrics.tasks_retried,
                "average_execution_time": self.metrics.average_execution_time,
                "system_utilization": self.metrics.system_utilization,
                "workflow_completion_rate": self.metrics.workflow_completion_rate,
                "last_update": self.metrics.last_update.isoformat()
            }
        }
        
        await self._set_redis_value(self.metrics_key, metrics_data)
    
    async def _save_alert(self, alert: MonitoringAlert):
        """保存告警"""
        alert_key = f"{self.alerts_key}:{alert.alert_id}"
        alert_data = {
            "alert_id": alert.alert_id,
            "alert_type": alert.alert_type,
            "severity": alert.severity,
            "message": alert.message,
            "details": alert.details,
            "created_at": alert.created_at.isoformat(),
            "resolved_at": alert.resolved_at.isoformat() if alert.resolved_at else None,
            "is_resolved": alert.is_resolved
        }
        
        await self._set_redis_value(alert_key, alert_data)
    
    async def _delete_alert(self, alert_id: str):
        """删除告警"""
        alert_key = f"{self.alerts_key}:{alert_id}"
        try:
            await self.redis_client.delete(alert_key)
        except Exception as e:
            self.logger.error(f"Error deleting alert {alert_id}: {str(e)}")
    
    # === 公共接口 ===
    
    async def get_monitoring_dashboard(self) -> Dict:
        """获取监控面板数据"""
        
        # 获取实时状态
        dependency_status = await self.dependency_manager.get_dependency_status()
        scheduler_metrics = await self.scheduler.get_scheduling_metrics()
        workflows = await self.workflow_engine.list_workflows()
        
        # 获取未解决的告警
        active_alerts = [
            {
                "alert_id": alert.alert_id,
                "alert_type": alert.alert_type,
                "severity": alert.severity,
                "message": alert.message,
                "created_at": alert.created_at.isoformat()
            }
            for alert in self.alerts.values() if not alert.is_resolved
        ]
        
        return {
            "team_id": self.team_id,
            "monitoring_status": {
                "is_running": self.is_running,
                "monitoring_mode": self.monitoring_mode.value,
                "monitoring_interval": self.monitoring_interval,
                "last_update": self.metrics.last_update.isoformat()
            },
            "system_metrics": {
                "total_tasks_processed": self.metrics.total_tasks_processed,
                "tasks_auto_executed": self.metrics.tasks_auto_executed,
                "tasks_failed": self.metrics.tasks_failed,
                "tasks_retried": self.metrics.tasks_retried,
                "average_execution_time": self.metrics.average_execution_time,
                "system_utilization": self.metrics.system_utilization,
                "workflow_completion_rate": self.metrics.workflow_completion_rate
            },
            "component_status": {
                "scheduler": {
                    "assigned_tasks": scheduler_metrics.assigned_tasks,
                    "failed_assignments": scheduler_metrics.failed_assignments,
                    "average_assignment_time": scheduler_metrics.average_assignment_time
                },
                "dependencies": {
                    "total_tasks": dependency_status["statistics"]["total_tasks"],
                    "ready_tasks": dependency_status["statistics"]["ready_tasks"],
                    "total_dependencies": dependency_status["statistics"]["total_dependencies"]
                },
                "workflows": {
                    "total_workflows": len(workflows),
                    "running_workflows": len([wf for wf in workflows if wf["status"] == "running"]),
                    "completed_workflows": len([wf for wf in workflows if wf["status"] == "completed"])
                }
            },
            "active_alerts": active_alerts,
            "configuration": self.config
        }
    
    async def update_configuration(self, config_updates: Dict):
        """更新监控配置"""
        
        self.config.update(config_updates)
        
        self.logger.info(
            f"Monitoring configuration updated",
            extra={
                'team_id': self.team_id,
                'config_updates': config_updates,
                'action': 'config_updated'
            }
        )
        
        # 保存配置
        config_key = f"{self.monitor_key}:config"
        await self._set_redis_value(config_key, self.config)
    
    async def _log_monitor_event(self, event_type: str, data: Dict):
        """记录监控事件"""
        self.business_logger.logger.info(
            f"Monitor event: {event_type}",
            extra={
                'team_id': self.team_id,
                'event_type': event_type,
                'event_data': data,
                'action': 'monitor_event'
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