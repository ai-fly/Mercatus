import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set
from dataclasses import dataclass
from uuid import uuid4

from app.types.blackboard import (
    BlackboardTask, TaskStatus, TaskPriority, ExpertRole, ExpertInstance,
    TaskAssignment, TaskFilter, TaskSearchCriteria
)
from app.core.blackboard import BlackBoard
from app.clients.redis_client import redis_client_instance
from app.utils.logging import get_business_logger, get_performance_logger


@dataclass
class SchedulingRule:
    """任务调度规则"""
    expert_role: ExpertRole
    max_load_threshold: float = 0.8  # 专家最大负载阈值
    priority_weight: float = 1.0    # 优先级权重
    specialization_weight: float = 0.5  # 专业技能权重
    availability_weight: float = 1.5   # 可用性权重


@dataclass
class SchedulingMetrics:
    """调度指标"""
    total_tasks: int = 0
    assigned_tasks: int = 0
    pending_tasks: int = 0
    failed_assignments: int = 0
    average_assignment_time: float = 0.0
    expert_utilization: Dict[str, float] = None
    
    def __post_init__(self):
        if self.expert_utilization is None:
            self.expert_utilization = {}


class AutoTaskScheduler:
    """
    自动任务调度器 - 负责监控待分配任务并自动分配给合适的专家实例
    
    核心功能：
    1. 持续监控待分配任务
    2. 基于负载均衡和专家能力自动分配任务
    3. 处理任务优先级和依赖关系
    4. 提供调度统计和性能指标
    """
    
    def __init__(self, team_id: str):
        """初始化自动任务调度器"""
        self.team_id = team_id
        self.redis_client = redis_client_instance.get_redis_client()
        self.logger = logging.getLogger(f"AutoScheduler-{team_id}")
        self.business_logger = get_business_logger()
        self.performance_logger = get_performance_logger()
        
        # 调度配置
        self.scheduling_rules = {
            ExpertRole.PLANNER: SchedulingRule(
                expert_role=ExpertRole.PLANNER,
                max_load_threshold=0.8,
                priority_weight=1.2,
                specialization_weight=0.8,
                availability_weight=1.5
            ),
            ExpertRole.EXECUTOR: SchedulingRule(
                expert_role=ExpertRole.EXECUTOR,
                max_load_threshold=0.9,
                priority_weight=1.0,
                specialization_weight=0.6,
                availability_weight=1.2
            ),
            ExpertRole.EVALUATOR: SchedulingRule(
                expert_role=ExpertRole.EVALUATOR,
                max_load_threshold=0.85,
                priority_weight=1.1,
                specialization_weight=0.7,
                availability_weight=1.3
            )
        }
        
        # 调度状态
        self.is_running = False
        self.scheduling_interval = 30  # 30秒检查一次
        self.metrics = SchedulingMetrics()
        
        # Redis键前缀
        self.scheduler_key = f"scheduler:{team_id}"
        self.metrics_key = f"scheduler_metrics:{team_id}"
        
        self.logger.info(f"AutoTaskScheduler initialized for team {team_id}")
    
    async def start_scheduler(self):
        """启动自动调度器"""
        if self.is_running:
            self.logger.warning("Scheduler is already running")
            return
        
        self.is_running = True
        self.logger.info("Starting AutoTaskScheduler")
        
        # 启动调度循环
        asyncio.create_task(self._scheduling_loop())
        
        # 记录启动事件
        await self._log_scheduler_event("scheduler_started", {
            "team_id": self.team_id,
            "scheduling_interval": self.scheduling_interval
        })
    
    async def stop_scheduler(self):
        """停止自动调度器"""
        self.is_running = False
        self.logger.info("Stopping AutoTaskScheduler")
        
        # 记录停止事件
        await self._log_scheduler_event("scheduler_stopped", {
            "team_id": self.team_id,
            "final_metrics": self.metrics.__dict__
        })
    
    async def _scheduling_loop(self):
        """主调度循环"""
        while self.is_running:
            try:
                start_time = datetime.now()
                
                # 执行一轮调度
                assigned_count = await self._run_scheduling_round()
                
                # 更新指标
                execution_time = (datetime.now() - start_time).total_seconds()
                await self._update_metrics(assigned_count, execution_time)
                
                # 等待下一轮
                await asyncio.sleep(self.scheduling_interval)
                
            except Exception as e:
                self.logger.error(f"Error in scheduling loop: {str(e)}", exc_info=True)
                await asyncio.sleep(self.scheduling_interval)
    
    async def _run_scheduling_round(self) -> int:
        """执行一轮任务调度"""
        with self.performance_logger.time_operation(
            "scheduling_round",
            team_id=self.team_id
        ):
            # 1. 获取待分配任务
            pending_tasks = await self._get_pending_tasks()
            if not pending_tasks:
                return 0
            
            self.logger.debug(f"Found {len(pending_tasks)} pending tasks")
            
            # 2. 按优先级排序任务
            sorted_tasks = self._sort_tasks_by_priority(pending_tasks)
            
            # 3. 为每个任务尝试分配专家
            assigned_count = 0
            for task in sorted_tasks:
                try:
                    if await self._assign_task_to_expert(task):
                        assigned_count += 1
                        self.logger.info(
                            f"Auto-assigned task {task.task_id} to expert",
                            extra={
                                'task_id': task.task_id,
                                'team_id': self.team_id,
                                'expert_role': task.required_expert_role.value,
                                'task_priority': task.priority.value,
                                'action': 'auto_assignment_success'
                            }
                        )
                except Exception as e:
                    self.logger.error(
                        f"Failed to assign task {task.task_id}: {str(e)}",
                        extra={
                            'task_id': task.task_id,
                            'team_id': self.team_id,
                            'error': str(e)
                        }
                    )
                    self.metrics.failed_assignments += 1
            
            return assigned_count
    
    async def _get_pending_tasks(self) -> List[BlackboardTask]:
        """获取待分配的任务"""
        from app.core.team_manager import team_manager
        
        blackboard = team_manager.get_blackboard(self.team_id)
        if not blackboard:
            return []
        
        # 搜索PENDING状态的任务
        task_filter = TaskFilter(status=[TaskStatus.PENDING])
        search_criteria = TaskSearchCriteria(filters=task_filter)
        
        tasks, _ = await blackboard.search_tasks(search_criteria)
        return tasks
    
    def _sort_tasks_by_priority(self, tasks: List[BlackboardTask]) -> List[BlackboardTask]:
        """按优先级排序任务"""
        priority_order = {
            TaskPriority.URGENT: 4,
            TaskPriority.HIGH: 3,
            TaskPriority.MEDIUM: 2,
            TaskPriority.LOW: 1
        }
        
        return sorted(
            tasks,
            key=lambda t: (
                priority_order.get(t.priority, 0),  # 优先级
                -t.created_at.timestamp()  # 创建时间（越早越高）
            ),
            reverse=True
        )
    
    async def _assign_task_to_expert(self, task: BlackboardTask) -> bool:
        """为任务分配专家实例"""
        from app.core.team_manager import team_manager
        
        # 获取BlackBoard
        blackboard = team_manager.get_blackboard(self.team_id)
        if not blackboard:
            return False
        
        # 获取适合的专家实例
        expert_instance = await self._find_best_expert_for_task(task)
        if not expert_instance:
            self.logger.warning(
                f"No available expert found for task {task.task_id}",
                extra={
                    'task_id': task.task_id,
                    'team_id': self.team_id,
                    'required_role': task.required_expert_role.value
                }
            )
            return False
        
        # 执行分配
        success = await blackboard.assign_task(
            task.task_id,
            expert_instance.instance_id,
            "auto_scheduler"
        )
        
        if success:
            # 记录分配事件
            self.business_logger.log_task_assigned(
                task.task_id, expert_instance.instance_id, self.team_id, "auto_scheduler"
            )
        
        return success
    
    async def _find_best_expert_for_task(self, task: BlackboardTask) -> Optional[ExpertInstance]:
        """为任务找到最佳的专家实例"""
        from app.core.team_manager import team_manager
        
        # 获取团队信息
        team = await team_manager.get_team(self.team_id)
        if not team:
            return None
        
        # 找到匹配角色的专家实例
        candidate_experts = [
            expert for expert in team.expert_instances
            if expert.expert_role == task.required_expert_role 
            and expert.status == "active"
        ]
        
        if not candidate_experts:
            return None
        
        # 获取调度规则
        rule = self.scheduling_rules.get(task.required_expert_role)
        if not rule:
            # 如果没有规则，选择负载最低的
            return min(candidate_experts, key=lambda e: e.current_task_count)
        
        # 计算每个专家的得分
        best_expert = None
        best_score = -1
        
        for expert in candidate_experts:
            score = await self._calculate_expert_score(expert, task, rule)
            
            self.logger.debug(
                f"Expert {expert.instance_name} score: {score:.3f}",
                extra={
                    'expert_id': expert.instance_id,
                    'expert_name': expert.instance_name,
                    'current_load': expert.current_task_count,
                    'max_tasks': expert.max_concurrent_tasks,
                    'score': score
                }
            )
            
            if score > best_score:
                best_score = score
                best_expert = expert
        
        return best_expert
    
    async def _calculate_expert_score(
        self, 
        expert: ExpertInstance, 
        task: BlackboardTask, 
        rule: SchedulingRule
    ) -> float:
        """计算专家实例对任务的适配得分"""
        
        # 1. 可用性得分 (0-1)
        load_ratio = expert.current_task_count / expert.max_concurrent_tasks
        if load_ratio >= rule.max_load_threshold:
            return 0  # 负载过高，不可分配
        
        availability_score = (1 - load_ratio) * rule.availability_weight
        
        # 2. 优先级匹配得分 (0-1)
        priority_scores = {
            TaskPriority.URGENT: 1.0,
            TaskPriority.HIGH: 0.8,
            TaskPriority.MEDIUM: 0.6,
            TaskPriority.LOW: 0.4
        }
        priority_score = priority_scores.get(task.priority, 0.5) * rule.priority_weight
        
        # 3. 专业技能匹配得分 (0-1)
        specialization_score = self._calculate_specialization_match(
            expert, task
        ) * rule.specialization_weight
        
        # 4. 历史性能得分 (0-1)
        performance_score = self._get_expert_performance_score(expert)
        
        # 综合得分
        total_score = (
            availability_score + 
            priority_score + 
            specialization_score + 
            performance_score
        ) / 4
        
        return total_score
    
    def _calculate_specialization_match(
        self, 
        expert: ExpertInstance, 
        task: BlackboardTask
    ) -> float:
        """计算专家专业技能与任务的匹配度"""
        
        # 获取任务要求的技能
        required_skills = set()
        if hasattr(task, 'metadata') and task.metadata:
            required_skills = set(task.metadata.context_data.get('required_skills', []))
        
        # 获取专家的专业技能
        expert_skills = set(expert.specializations)
        
        if not required_skills:
            return 0.8  # 如果没有特定技能要求，返回基础分数
        
        if not expert_skills:
            return 0.5  # 如果专家没有定义技能，返回中等分数
        
        # 计算技能匹配度
        matched_skills = required_skills.intersection(expert_skills)
        match_ratio = len(matched_skills) / len(required_skills)
        
        return match_ratio
    
    def _get_expert_performance_score(self, expert: ExpertInstance) -> float:
        """获取专家的历史性能得分"""
        
        if not expert.performance_metrics:
            return 0.7  # 新专家默认得分
        
        # 计算完成率
        completed_tasks = expert.performance_metrics.get('completed_tasks', 0)
        failed_tasks = expert.performance_metrics.get('failed_tasks', 0)
        total_tasks = completed_tasks + failed_tasks
        
        if total_tasks == 0:
            return 0.7
        
        completion_rate = completed_tasks / total_tasks
        
        # 考虑任务质量评分
        avg_quality = expert.performance_metrics.get('average_quality', 0.7)
        
        # 综合性能得分
        performance_score = (completion_rate * 0.6) + (avg_quality * 0.4)
        
        return min(performance_score, 1.0)
    
    async def _update_metrics(self, assigned_count: int, execution_time: float):
        """更新调度指标"""
        
        # 更新基础指标
        self.metrics.assigned_tasks += assigned_count
        
        # 更新平均分配时间
        if assigned_count > 0:
            self.metrics.average_assignment_time = (
                (self.metrics.average_assignment_time * self.metrics.assigned_tasks + execution_time) /
                (self.metrics.assigned_tasks + assigned_count)
            )
        
        # 保存指标到Redis
        await self._save_metrics()
    
    async def _save_metrics(self):
        """保存调度指标到Redis"""
        metrics_data = {
            "team_id": self.team_id,
            "timestamp": datetime.now().isoformat(),
            "metrics": self.metrics.__dict__
        }
        
        await self._set_redis_value(
            self.metrics_key,
            metrics_data,
            expire_seconds=86400  # 24小时过期
        )
    
    async def _log_scheduler_event(self, event_type: str, data: Dict):
        """记录调度器事件"""
        event_data = {
            "event_type": event_type,
            "team_id": self.team_id,
            "timestamp": datetime.now().isoformat(),
            "data": data
        }
        
        self.business_logger.logger.info(
            f"Scheduler event: {event_type}",
            extra={
                'team_id': self.team_id,
                'event_type': event_type,
                'event_data': data,
                'action': 'scheduler_event'
            }
        )
    
    # === 公共接口 ===
    
    async def get_scheduling_metrics(self) -> SchedulingMetrics:
        """获取调度指标"""
        # 更新当前指标
        from app.core.team_manager import team_manager
        
        team = await team_manager.get_team(self.team_id)
        if team:
            # 计算专家利用率
            for expert in team.expert_instances:
                if expert.max_concurrent_tasks > 0:
                    utilization = expert.current_task_count / expert.max_concurrent_tasks
                    self.metrics.expert_utilization[expert.instance_id] = utilization
        
        return self.metrics
    
    async def force_scheduling_round(self) -> Dict:
        """强制执行一轮调度"""
        self.logger.info("Force scheduling round requested")
        
        start_time = datetime.now()
        assigned_count = await self._run_scheduling_round()
        execution_time = (datetime.now() - start_time).total_seconds()
        
        return {
            "assigned_tasks": assigned_count,
            "execution_time": execution_time,
            "timestamp": datetime.now().isoformat()
        }
    
    # === Redis辅助方法 ===
    
    async def _set_redis_value(self, key: str, value, expire_seconds: int = None):
        """设置Redis值"""
        try:
            import json
            if isinstance(value, dict):
                value = json.dumps(value, default=str)
            
            await self.redis_client.set(key, value)
            if expire_seconds:
                await self.redis_client.expire(key, expire_seconds)
        except Exception as e:
            self.logger.error(f"Redis set error: {str(e)}")
    
    async def _get_redis_value(self, key: str):
        """获取Redis值"""
        try:
            import json
            value = await self.redis_client.get(key)
            if value:
                try:
                    return json.loads(value)
                except:
                    return value
            return None
        except Exception as e:
            self.logger.error(f"Redis get error: {str(e)}")
            return None 