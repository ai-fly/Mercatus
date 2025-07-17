import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set, Tuple, Union
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


class DependencyCondition(Enum):
    """依赖条件类型"""
    TASK_COMPLETED = "task_completed"           # 任务完成
    TASK_STARTED = "task_started"               # 任务开始
    TASK_FAILED = "task_failed"                 # 任务失败
    TIME_DELAY = "time_delay"                   # 时间延迟
    EXPERT_AVAILABLE = "expert_available"       # 专家可用
    RESOURCE_AVAILABLE = "resource_available"   # 资源可用
    CUSTOM_CONDITION = "custom_condition"       # 自定义条件


@dataclass
class DependencyRule:
    """依赖规则"""
    dependency_id: str
    source_task_id: str              # 源任务ID
    target_task_id: str              # 目标任务ID
    condition: DependencyCondition    # 依赖条件
    condition_params: Dict = field(default_factory=dict)  # 条件参数
    is_blocking: bool = True         # 是否阻塞性依赖
    weight: float = 1.0              # 依赖权重
    created_at: datetime = field(default_factory=datetime.now)
    
    def is_satisfied(self, task_states: Dict[str, TaskStatus], current_time: datetime) -> bool:
        """检查依赖条件是否满足"""
        source_status = task_states.get(self.source_task_id)
        
        if self.condition == DependencyCondition.TASK_COMPLETED:
            return source_status == TaskStatus.COMPLETED
        
        elif self.condition == DependencyCondition.TASK_STARTED:
            return source_status in [TaskStatus.IN_PROGRESS, TaskStatus.COMPLETED]
        
        elif self.condition == DependencyCondition.TASK_FAILED:
            return source_status == TaskStatus.FAILED
        
        elif self.condition == DependencyCondition.TIME_DELAY:
            delay_minutes = self.condition_params.get('delay_minutes', 0)
            required_time = self.created_at + timedelta(minutes=delay_minutes)
            return current_time >= required_time
        
        elif self.condition == DependencyCondition.CUSTOM_CONDITION:
            # 这里可以扩展自定义条件逻辑
            return self._evaluate_custom_condition(task_states, current_time)
        
        return False
    
    def _evaluate_custom_condition(self, task_states: Dict[str, TaskStatus], current_time: datetime) -> bool:
        """评估自定义条件"""
        condition_type = self.condition_params.get('type')
        
        if condition_type == 'all_parallel_completed':
            # 所有并行任务完成
            parallel_tasks = self.condition_params.get('parallel_tasks', [])
            return all(task_states.get(task_id) == TaskStatus.COMPLETED for task_id in parallel_tasks)
        
        elif condition_type == 'any_parallel_completed':
            # 任意并行任务完成
            parallel_tasks = self.condition_params.get('parallel_tasks', [])
            return any(task_states.get(task_id) == TaskStatus.COMPLETED for task_id in parallel_tasks)
        
        elif condition_type == 'quality_threshold':
            # 质量阈值检查
            if task_states.get(self.source_task_id) != TaskStatus.COMPLETED:
                return False
            # 这里需要从任务结果中获取质量分数
            threshold = self.condition_params.get('quality_threshold', 0.8)
            # 简化实现，实际需要获取任务质量评分
            return True
        
        return False


@dataclass
class DependencyGraph:
    """依赖图"""
    nodes: Dict[str, BlackboardTask] = field(default_factory=dict)  # task_id -> task
    edges: Dict[str, List[DependencyRule]] = field(default_factory=dict)  # target_task_id -> [rules]
    reverse_edges: Dict[str, List[DependencyRule]] = field(default_factory=dict)  # source_task_id -> [rules]
    
    def add_task(self, task: BlackboardTask):
        """添加任务节点"""
        self.nodes[task.task_id] = task
        if task.task_id not in self.edges:
            self.edges[task.task_id] = []
        if task.task_id not in self.reverse_edges:
            self.reverse_edges[task.task_id] = []
    
    def add_dependency(self, rule: DependencyRule):
        """添加依赖关系"""
        if rule.target_task_id not in self.edges:
            self.edges[rule.target_task_id] = []
        self.edges[rule.target_task_id].append(rule)
        
        if rule.source_task_id not in self.reverse_edges:
            self.reverse_edges[rule.source_task_id] = []
        self.reverse_edges[rule.source_task_id].append(rule)
    
    def get_dependencies(self, task_id: str) -> List[DependencyRule]:
        """获取任务的所有依赖"""
        return self.edges.get(task_id, [])
    
    def get_dependents(self, task_id: str) -> List[DependencyRule]:
        """获取依赖于指定任务的所有任务"""
        return self.reverse_edges.get(task_id, [])
    
    def has_cycle(self) -> bool:
        """检查是否存在循环依赖"""
        visited = set()
        rec_stack = set()
        
        def dfs(node_id: str) -> bool:
            visited.add(node_id)
            rec_stack.add(node_id)
            
            for rule in self.reverse_edges.get(node_id, []):
                target_id = rule.target_task_id
                if target_id not in visited:
                    if dfs(target_id):
                        return True
                elif target_id in rec_stack:
                    return True
            
            rec_stack.remove(node_id)
            return False
        
        for node_id in self.nodes:
            if node_id not in visited:
                if dfs(node_id):
                    return True
        
        return False
    
    def topological_sort(self) -> List[str]:
        """拓扑排序，返回任务执行顺序"""
        in_degree = {}
        
        # 计算入度
        for task_id in self.nodes:
            in_degree[task_id] = len(self.edges.get(task_id, []))
        
        # 找到入度为0的节点
        queue = [task_id for task_id, degree in in_degree.items() if degree == 0]
        result = []
        
        while queue:
            current = queue.pop(0)
            result.append(current)
            
            # 减少相邻节点的入度
            for rule in self.reverse_edges.get(current, []):
                target_id = rule.target_task_id
                in_degree[target_id] -= 1
                if in_degree[target_id] == 0:
                    queue.append(target_id)
        
        # 检查是否存在循环
        if len(result) != len(self.nodes):
            return []  # 存在循环依赖
        
        return result


class TaskDependencyManager:
    """
    任务依赖管理器 - 处理任务间的前置条件和依赖关系
    
    核心功能：
    1. 管理任务依赖关系
    2. 检查依赖条件满足情况
    3. 提供任务执行建议
    4. 检测和处理循环依赖
    5. 支持复杂的依赖逻辑
    """
    
    def __init__(self, team_id: str):
        """初始化任务依赖管理器"""
        self.team_id = team_id
        self.redis_client = redis_client_instance.get_redis_client()
        self.logger = logging.getLogger(f"DependencyManager-{team_id}")
        self.business_logger = get_business_logger()
        self.performance_logger = get_performance_logger()
        
        # 依赖图
        self.dependency_graph = DependencyGraph()
        
        # 缓存
        self._task_states_cache: Dict[str, TaskStatus] = {}
        self._cache_timestamp = datetime.now()
        self._cache_ttl = timedelta(minutes=1)  # 缓存1分钟
        
        # Redis键前缀
        self.dependency_prefix = f"dependency:{team_id}"
        self.graph_key = f"dependency_graph:{team_id}"
        
        self.logger.info(f"TaskDependencyManager initialized for team {team_id}")
    
    async def initialize(self):
        """初始化依赖管理器，加载已保存的依赖关系"""
        await self._load_dependency_graph()
        await self._refresh_task_states()
        
        self.logger.info(
            f"Dependency manager initialized with {len(self.dependency_graph.nodes)} tasks"
        )
    
    # === 依赖关系管理 ===
    
    async def add_task_dependency(
        self,
        source_task_id: str,
        target_task_id: str,
        condition: DependencyCondition,
        condition_params: Dict = None,
        is_blocking: bool = True,
        weight: float = 1.0
    ) -> str:
        """添加任务依赖关系"""
        
        # 检查任务是否存在
        from app.core.team_manager import team_manager
        blackboard = team_manager.get_blackboard(self.team_id)
        
        if not blackboard:
            raise ValueError(f"Team {self.team_id} not found")
        
        source_task = await blackboard.get_task(source_task_id)
        target_task = await blackboard.get_task(target_task_id)
        
        if not source_task:
            raise ValueError(f"Source task {source_task_id} not found")
        if not target_task:
            raise ValueError(f"Target task {target_task_id} not found")
        
        # 创建依赖规则
        dependency_rule = DependencyRule(
            dependency_id=str(uuid4()),
            source_task_id=source_task_id,
            target_task_id=target_task_id,
            condition=condition,
            condition_params=condition_params or {},
            is_blocking=is_blocking,
            weight=weight
        )
        
        # 添加到依赖图
        self.dependency_graph.add_task(source_task)
        self.dependency_graph.add_task(target_task)
        self.dependency_graph.add_dependency(dependency_rule)
        
        # 检查循环依赖
        if self.dependency_graph.has_cycle():
            # 回滚添加的依赖
            self.dependency_graph.edges[target_task_id].remove(dependency_rule)
            self.dependency_graph.reverse_edges[source_task_id].remove(dependency_rule)
            raise ValueError("Adding this dependency would create a cycle")
        
        # 保存依赖图
        await self._save_dependency_graph()
        
        self.logger.info(
            f"Added dependency: {source_task_id} -> {target_task_id}",
            extra={
                'source_task_id': source_task_id,
                'target_task_id': target_task_id,
                'condition': condition.value,
                'is_blocking': is_blocking,
                'team_id': self.team_id,
                'action': 'dependency_added'
            }
        )
        
        return dependency_rule.dependency_id
    
    async def remove_task_dependency(self, dependency_id: str) -> bool:
        """移除任务依赖关系"""
        
        # 查找并移除依赖
        for target_task_id, rules in self.dependency_graph.edges.items():
            for rule in rules:
                if rule.dependency_id == dependency_id:
                    # 从两个方向移除
                    self.dependency_graph.edges[target_task_id].remove(rule)
                    self.dependency_graph.reverse_edges[rule.source_task_id].remove(rule)
                    
                    # 保存更新
                    await self._save_dependency_graph()
                    
                    self.logger.info(
                        f"Removed dependency {dependency_id}: {rule.source_task_id} -> {rule.target_task_id}",
                        extra={
                            'dependency_id': dependency_id,
                            'source_task_id': rule.source_task_id,
                            'target_task_id': rule.target_task_id,
                            'team_id': self.team_id,
                            'action': 'dependency_removed'
                        }
                    )
                    
                    return True
        
        return False
    
    async def add_workflow_dependencies(
        self,
        workflow_id: str,
        task_chain: List[str],
        condition: DependencyCondition = DependencyCondition.TASK_COMPLETED
    ):
        """为工作流添加链式依赖关系"""
        
        if len(task_chain) < 2:
            return
        
        dependencies_added = []
        
        try:
            for i in range(len(task_chain) - 1):
                source_task_id = task_chain[i]
                target_task_id = task_chain[i + 1]
                
                dependency_id = await self.add_task_dependency(
                    source_task_id=source_task_id,
                    target_task_id=target_task_id,
                    condition=condition,
                    condition_params={'workflow_id': workflow_id},
                    is_blocking=True
                )
                
                dependencies_added.append(dependency_id)
            
            self.logger.info(
                f"Added workflow dependencies for {workflow_id}: {len(dependencies_added)} dependencies",
                extra={
                    'workflow_id': workflow_id,
                    'task_count': len(task_chain),
                    'dependencies_added': len(dependencies_added),
                    'team_id': self.team_id,
                    'action': 'workflow_dependencies_added'
                }
            )
            
        except Exception as e:
            # 回滚已添加的依赖
            for dep_id in dependencies_added:
                await self.remove_task_dependency(dep_id)
            raise e
    
    # === 依赖检查和分析 ===
    
    async def check_task_ready(self, task_id: str) -> Tuple[bool, List[str], List[DependencyRule]]:
        """检查任务是否准备好执行"""
        
        await self._refresh_task_states()
        
        dependencies = self.dependency_graph.get_dependencies(task_id)
        if not dependencies:
            return True, [], []  # 无依赖，可以执行
        
        ready = True
        unmet_reasons = []
        unmet_dependencies = []
        
        current_time = datetime.now()
        
        for rule in dependencies:
            if not rule.is_blocking:
                continue  # 非阻塞性依赖不影响执行
            
            if not rule.is_satisfied(self._task_states_cache, current_time):
                ready = False
                unmet_dependencies.append(rule)
                
                # 生成未满足原因
                if rule.condition == DependencyCondition.TASK_COMPLETED:
                    source_status = self._task_states_cache.get(rule.source_task_id, TaskStatus.PENDING)
                    unmet_reasons.append(f"Task {rule.source_task_id} status: {source_status.value}")
                
                elif rule.condition == DependencyCondition.TIME_DELAY:
                    delay_minutes = rule.condition_params.get('delay_minutes', 0)
                    required_time = rule.created_at + timedelta(minutes=delay_minutes)
                    remaining = (required_time - current_time).total_seconds() / 60
                    unmet_reasons.append(f"Time delay: {remaining:.1f} minutes remaining")
                
                else:
                    unmet_reasons.append(f"Condition {rule.condition.value} not met")
        
        return ready, unmet_reasons, unmet_dependencies
    
    async def get_ready_tasks(self) -> List[str]:
        """获取所有准备好执行的任务"""
        
        await self._refresh_task_states()
        
        ready_tasks = []
        
        for task_id in self.dependency_graph.nodes:
            task_status = self._task_states_cache.get(task_id, TaskStatus.PENDING)
            
            # 只检查PENDING状态的任务
            if task_status == TaskStatus.PENDING:
                is_ready, _, _ = await self.check_task_ready(task_id)
                if is_ready:
                    ready_tasks.append(task_id)
        
        return ready_tasks
    
    async def get_execution_order(self) -> List[str]:
        """获取建议的任务执行顺序"""
        
        # 首先进行拓扑排序
        topo_order = self.dependency_graph.topological_sort()
        
        if not topo_order:
            self.logger.warning("Cannot determine execution order due to circular dependencies")
            return []
        
        # 根据当前状态过滤已完成的任务
        await self._refresh_task_states()
        
        pending_order = []
        for task_id in topo_order:
            status = self._task_states_cache.get(task_id, TaskStatus.PENDING)
            if status in [TaskStatus.PENDING, TaskStatus.ASSIGNED]:
                pending_order.append(task_id)
        
        return pending_order
    
    async def analyze_dependencies(self, task_id: str) -> Dict:
        """分析任务的依赖关系"""
        
        await self._refresh_task_states()
        
        # 获取直接依赖
        direct_dependencies = self.dependency_graph.get_dependencies(task_id)
        
        # 获取依赖于此任务的任务
        dependents = self.dependency_graph.get_dependents(task_id)
        
        # 分析依赖链
        dependency_chain = await self._trace_dependency_chain(task_id)
        
        # 计算关键路径
        critical_path = await self._calculate_critical_path(task_id)
        
        return {
            "task_id": task_id,
            "direct_dependencies": [
                {
                    "dependency_id": rule.dependency_id,
                    "source_task_id": rule.source_task_id,
                    "condition": rule.condition.value,
                    "is_blocking": rule.is_blocking,
                    "is_satisfied": rule.is_satisfied(self._task_states_cache, datetime.now()),
                    "weight": rule.weight
                }
                for rule in direct_dependencies
            ],
            "dependents": [
                {
                    "dependency_id": rule.dependency_id,
                    "target_task_id": rule.target_task_id,
                    "condition": rule.condition.value,
                    "is_blocking": rule.is_blocking
                }
                for rule in dependents
            ],
            "dependency_chain": dependency_chain,
            "critical_path": critical_path,
            "can_execute": await self.check_task_ready(task_id)
        }
    
    async def _trace_dependency_chain(self, task_id: str, visited: Set[str] = None) -> List[str]:
        """追踪依赖链"""
        if visited is None:
            visited = set()
        
        if task_id in visited:
            return []  # 避免循环
        
        visited.add(task_id)
        chain = [task_id]
        
        dependencies = self.dependency_graph.get_dependencies(task_id)
        for rule in dependencies:
            if rule.is_blocking:  # 只追踪阻塞性依赖
                sub_chain = await self._trace_dependency_chain(rule.source_task_id, visited.copy())
                chain.extend(sub_chain)
        
        return chain
    
    async def _calculate_critical_path(self, task_id: str) -> List[str]:
        """计算关键路径（最长依赖路径）"""
        
        def get_path_length(current_id: str, memo: Dict[str, int] = None) -> int:
            if memo is None:
                memo = {}
            
            if current_id in memo:
                return memo[current_id]
            
            dependencies = self.dependency_graph.get_dependencies(current_id)
            if not dependencies:
                memo[current_id] = 1
                return 1
            
            max_length = 0
            for rule in dependencies:
                if rule.is_blocking:
                    length = get_path_length(rule.source_task_id, memo)
                    max_length = max(max_length, length)
            
            memo[current_id] = max_length + 1
            return max_length + 1
        
        # 找到最长路径
        memo = {}
        get_path_length(task_id, memo)
        
        # 重构路径
        def reconstruct_path(current_id: str) -> List[str]:
            dependencies = self.dependency_graph.get_dependencies(current_id)
            if not dependencies:
                return [current_id]
            
            max_length = 0
            best_dependency = None
            
            for rule in dependencies:
                if rule.is_blocking:
                    length = memo.get(rule.source_task_id, 0)
                    if length > max_length:
                        max_length = length
                        best_dependency = rule
            
            if best_dependency:
                path = reconstruct_path(best_dependency.source_task_id)
                path.append(current_id)
                return path
            else:
                return [current_id]
        
        return reconstruct_path(task_id)
    
    # === 状态管理和缓存 ===
    
    async def _refresh_task_states(self):
        """刷新任务状态缓存"""
        
        current_time = datetime.now()
        if current_time - self._cache_timestamp < self._cache_ttl:
            return  # 缓存仍然有效
        
        from app.core.team_manager import team_manager
        blackboard = team_manager.get_blackboard(self.team_id)
        
        if not blackboard:
            return
        
        # 获取所有任务的当前状态
        for task_id in self.dependency_graph.nodes:
            task = await blackboard.get_task(task_id)
            if task:
                self._task_states_cache[task_id] = task.status
        
        self._cache_timestamp = current_time
        
        self.logger.debug(f"Refreshed task states cache for {len(self._task_states_cache)} tasks")
    
    async def invalidate_cache(self):
        """使缓存失效"""
        self._cache_timestamp = datetime.min
        await self._refresh_task_states()
    
    # === 持久化管理 ===
    
    async def _save_dependency_graph(self):
        """保存依赖图到Redis"""
        
        graph_data = {
            "team_id": self.team_id,
            "timestamp": datetime.now().isoformat(),
            "nodes": {
                task_id: {
                    "task_id": task.task_id,
                    "title": task.title,
                    "status": task.status.value,
                    "expert_role": task.required_expert_role.value
                }
                for task_id, task in self.dependency_graph.nodes.items()
            },
            "dependencies": []
        }
        
        # 收集所有依赖规则
        all_rules = []
        for rules_list in self.dependency_graph.edges.values():
            all_rules.extend(rules_list)
        
        # 去重（使用dependency_id）
        unique_rules = {}
        for rule in all_rules:
            unique_rules[rule.dependency_id] = rule
        
        graph_data["dependencies"] = [
            {
                "dependency_id": rule.dependency_id,
                "source_task_id": rule.source_task_id,
                "target_task_id": rule.target_task_id,
                "condition": rule.condition.value,
                "condition_params": rule.condition_params,
                "is_blocking": rule.is_blocking,
                "weight": rule.weight,
                "created_at": rule.created_at.isoformat()
            }
            for rule in unique_rules.values()
        ]
        
        await self._set_redis_value(self.graph_key, graph_data)
        
        self.logger.debug(f"Saved dependency graph with {len(unique_rules)} dependencies")
    
    async def _load_dependency_graph(self):
        """从Redis加载依赖图"""
        
        try:
            graph_data = await self._get_redis_value(self.graph_key)
            if not graph_data:
                return
            
            # 加载任务节点
            from app.core.team_manager import team_manager
            blackboard = team_manager.get_blackboard(self.team_id)
            
            if blackboard:
                for task_data in graph_data.get("nodes", {}).values():
                    task = await blackboard.get_task(task_data["task_id"])
                    if task:
                        self.dependency_graph.add_task(task)
            
            # 加载依赖关系
            for dep_data in graph_data.get("dependencies", []):
                rule = DependencyRule(
                    dependency_id=dep_data["dependency_id"],
                    source_task_id=dep_data["source_task_id"],
                    target_task_id=dep_data["target_task_id"],
                    condition=DependencyCondition(dep_data["condition"]),
                    condition_params=dep_data.get("condition_params", {}),
                    is_blocking=dep_data.get("is_blocking", True),
                    weight=dep_data.get("weight", 1.0),
                    created_at=datetime.fromisoformat(dep_data["created_at"])
                )
                self.dependency_graph.add_dependency(rule)
            
            self.logger.info(
                f"Loaded dependency graph: {len(self.dependency_graph.nodes)} tasks, "
                f"{len(graph_data.get('dependencies', []))} dependencies"
            )
            
        except Exception as e:
            self.logger.error(f"Error loading dependency graph: {str(e)}")
    
    # === 公共接口 ===
    
    async def get_dependency_status(self) -> Dict:
        """获取依赖管理器状态"""
        
        await self._refresh_task_states()
        
        ready_tasks = await self.get_ready_tasks()
        execution_order = await self.get_execution_order()
        
        # 统计信息
        total_tasks = len(self.dependency_graph.nodes)
        total_dependencies = sum(len(rules) for rules in self.dependency_graph.edges.values())
        
        status_counts = {}
        for status in self._task_states_cache.values():
            status_counts[status.value] = status_counts.get(status.value, 0) + 1
        
        return {
            "team_id": self.team_id,
            "statistics": {
                "total_tasks": total_tasks,
                "total_dependencies": total_dependencies,
                "ready_tasks": len(ready_tasks),
                "status_distribution": status_counts
            },
            "ready_tasks": ready_tasks,
            "suggested_execution_order": execution_order[:10],  # 前10个
            "cache_info": {
                "last_refresh": self._cache_timestamp.isoformat(),
                "cache_ttl_seconds": self._cache_ttl.total_seconds()
            }
        }
    
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