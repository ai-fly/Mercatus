"""
混合存储服务
结合 PostgreSQL 持久化存储和 Redis 缓存
提供高性能的数据访问和持久化保证
"""

import json
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
import uuid

from app.database.repositories import (
    UserRepository
)
from app.database.connection import AsyncSessionLocal
from app.clients.redis_client import redis_client_instance
from app.utils.logging import get_business_logger, get_performance_logger


class HybridStorageService:
    """
    混合存储服务
    核心功能：
    1. PostgreSQL 作为主存储，保证数据持久化
    2. Redis 作为缓存层，提供高性能访问
    3. 自动同步机制，确保数据一致性
    4. 智能缓存策略，优化性能
    """

    def __init__(self):
        self.redis_client = redis_client_instance.get_redis_client()
        self.logger = logging.getLogger("HybridStorage")
        self.business_logger = get_business_logger()
        self.performance_logger = get_performance_logger()

        # 缓存配置
        self.cache_ttl = 3600  # 1小时
        self.cache_prefix = "mercatus"

    # === 用户管理 ===

    async def create_user(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """创建用户"""
        async with AsyncSessionLocal() as session:
            try:
                user_repo = UserRepository(session)

                # 检查用户是否已存在
                existing_user = await user_repo.get_user_by_email(user_data["email"])
                if existing_user:
                    return {"status": "error", "message": "User with this email already exists"}

                # 创建用户
                user = await user_repo.create_user(
                    user_id=user_data.get("user_id", str(uuid.uuid4())),
                    username=user_data.get("email"), # or some other logic for username
                    email=user_data["email"],
                    full_name=user_data.get("full_name"),
                    picture_url=user_data.get("picture_url"),
                )

                # 缓存用户信息
                self._cache_user(user)

                return {
                    "status": "success",
                    "user": self._user_to_dict(user),
                    "message": "User created successfully"
                }

            except Exception as e:
                self.logger.error(f"Failed to create user: {str(e)}")
                return {"status": "error", "message": str(e)}

    async def get_user(self, user_id: str) -> Optional[Dict[str, Any]]:
        """获取用户信息"""
        try:
            # 先尝试从缓存获取
            cached_user = await self._get_cached_user(user_id)
            if cached_user:
                return cached_user

            # 从数据库获取
            user = await self.user_repo.get_user_by_id(user_id)
            if user:
                # 缓存用户信息
                await self._cache_user(user)
                return self._user_to_dict(user)

            return None

        except Exception as e:
            self.logger.error(f"Failed to get user: {str(e)}")
            return None

    async def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """根据邮箱获取用户信息"""
        try:
            async with AsyncSessionLocal() as session:
                user_repo = UserRepository(session)
                user = await user_repo.get_user_by_email(email)
                if user:
                    return self._user_to_dict(user)
                return None
        except Exception as e:
            self.logger.error(f"Failed to get user by email: {str(e)}")
            return None

    async def get_or_create_user_by_email(self, user_details: Dict[str, Any]) -> Dict[str, Any]:
        """根据邮箱获取用户，不存在则自动注册"""
        user = await self.get_user_by_email(user_details["email"])
        if user:
            return {"status": "success", "user": user, "message": "User exists"}
        
        # 自动注册
        user_details_to_create = user_details.copy()
        user_details_to_create["user_id"] = str(uuid.uuid4())
        
        created = await self.create_user(user_details_to_create)
        return created

    # === 团队管理 ===

    async def create_team(self, team_data: Dict[str, Any]) -> Dict[str, Any]:
        """创建团队"""
        try:
            # 创建团队
            team = await self.team_repo.create_team(team_data)

            # 添加团队所有者为成员
            await self.team_repo.add_team_member(
                team.team_id, 
                team.owner_id, 
                role="owner"
            )

            # 缓存团队信息
            await self._cache_team(team)

            return {
                "status": "success",
                "team": self._team_to_dict(team),
                "message": "Team created successfully"
            }

        except Exception as e:
            self.logger.error(f"Failed to create team: {str(e)}")
            return {"status": "error", "message": str(e)}

    async def get_team(self, team_id: str) -> Optional[Dict[str, Any]]:
        """获取团队信息"""
        try:
            # 先尝试从缓存获取
            cached_team = await self._get_cached_team(team_id)
            if cached_team:
                return cached_team

            # 从数据库获取
            team = await self.team_repo.get_team_by_id(team_id)
            if team:
                # 缓存团队信息
                await self._cache_team(team)
                return self._team_to_dict(team)

            return None

        except Exception as e:
            self.logger.error(f"Failed to get team: {str(e)}")
            return None

    async def get_user_teams(self, user_id: str) -> List[Dict[str, Any]]:
        """获取用户的所有团队"""
        try:
            teams = await self.user_repo.get_user_teams(user_id)
            return [self._team_to_dict(team) for team in teams]

        except Exception as e:
            self.logger.error(f"Failed to get user teams: {str(e)}")
            return []

    # === 任务管理 ===

    async def create_task(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """创建任务"""
        try:
            # 创建任务
            task = await self.task_repo.create_task(task_data)

            # 创建任务事件
            await self.task_repo.create_task_event({
                "event_id": f"event_{task.task_id}",
                "task_id": task.task_id,
                "event_type": "created",
                "event_data": {"creator_id": task_data.get("creator_id", "system")},
                "triggered_by": task_data.get("creator_id", "system")
            })

            # 缓存任务信息
            await self._cache_task(task)

            return {
                "status": "success",
                "task": self._task_to_dict(task),
                "message": "Task created successfully"
            }

        except Exception as e:
            self.logger.error(f"Failed to create task: {str(e)}")
            return {"status": "error", "message": str(e)}

    async def get_task(self, task_id: str) -> Optional[Dict[str, Any]]:
        """获取任务信息"""
        try:
            # 先尝试从缓存获取
            cached_task = await self._get_cached_task(task_id)
            if cached_task:
                return cached_task

            # 从数据库获取
            task = await self.task_repo.get_task_by_id(task_id)
            if task:
                # 缓存任务信息
                await self._cache_task(task)
                return self._task_to_dict(task)

            return None

        except Exception as e:
            self.logger.error(f"Failed to get task: {str(e)}")
            return None

    async def update_task_status(self, task_id: str, status: str, **kwargs) -> Optional[Dict[str, Any]]:
        """更新任务状态"""
        try:
            # 更新数据库
            task = await self.task_repo.update_task_status(task_id, status, **kwargs)
            if task:
                # 创建状态变更事件
                await self.task_repo.create_task_event({
                    "event_id": f"event_{task_id}_{datetime.now().timestamp()}",
                    "task_id": task_id,
                    "event_type": f"status_changed_to_{status}",
                    "event_data": kwargs,
                    "triggered_by": kwargs.get("updated_by", "system")
                })

                # 更新缓存
                await self._cache_task(task)
                return self._task_to_dict(task)

            return None

        except Exception as e:
            self.logger.error(f"Failed to update task status: {str(e)}")
            return None

    async def get_team_tasks(self, team_id: str, status: Optional[str] = None) -> List[Dict[str, Any]]:
        """获取团队任务"""
        try:
            tasks = await self.task_repo.get_team_tasks(team_id, status)
            return [self._task_to_dict(task) for task in tasks]

        except Exception as e:
            self.logger.error(f"Failed to get team tasks: {str(e)}")
            return []

    # === 专家实例管理 ===

    async def create_expert_instance(self, expert_data: Dict[str, Any]) -> Dict[str, Any]:
        """创建专家实例"""
        try:
            expert = await self.expert_repo.create_expert_instance(expert_data)

            # 缓存专家信息
            await self._cache_expert(expert)

            return {
                "status": "success",
                "expert": self._expert_to_dict(expert),
                "message": "Expert instance created successfully"
            }

        except Exception as e:
            self.logger.error(f"Failed to create expert instance: {str(e)}")
            return {"status": "error", "message": str(e)}

    async def get_expert_instance(self, instance_id: str) -> Optional[Dict[str, Any]]:
        """获取专家实例"""
        try:
            # 先尝试从缓存获取
            cached_expert = await self._get_cached_expert(instance_id)
            if cached_expert:
                return cached_expert

            # 从数据库获取
            expert = await self.expert_repo.get_expert_by_id(instance_id)
            if expert:
                # 缓存专家信息
                await self._cache_expert(expert)
                return self._expert_to_dict(expert)

            return None

        except Exception as e:
            self.logger.error(f"Failed to get expert instance: {str(e)}")
            return None

    async def get_team_experts(self, team_id: str, role: Optional[str] = None) -> List[Dict[str, Any]]:
        """获取团队专家实例"""
        try:
            experts = await self.expert_repo.get_team_experts(team_id, role)
            return [self._expert_to_dict(expert) for expert in experts]

        except Exception as e:
            self.logger.error(f"Failed to get team experts: {str(e)}")
            return []

    # === 缓存管理 ===

    def _cache_user(self, user) -> None:
        """缓存用户信息"""
        cache_key = f"{self.cache_prefix}:user:{user.user_id}"
        user_data = self._user_to_dict(user)
        self.redis_client.setex(cache_key, self.cache_ttl, json.dumps(user_data))

    def _get_cached_user(self, user_id: str) -> Optional[Dict[str, Any]]:
        """获取缓存的用户信息"""
        cache_key = f"{self.cache_prefix}:user:{user_id}"
        data = self.redis_client.get(cache_key)
        return json.loads(data) if data else None

    def _cache_team(self, team) -> None:
        """缓存团队信息"""
        cache_key = f"{self.cache_prefix}:team:{team.team_id}"
        team_data = self._team_to_dict(team)
        self.redis_client.setex(cache_key, self.cache_ttl, json.dumps(team_data))

    def _get_cached_team(self, team_id: str) -> Optional[Dict[str, Any]]:
        """获取缓存的团队信息"""
        cache_key = f"{self.cache_prefix}:team:{team_id}"
        data = self.redis_client.get(cache_key)
        return json.loads(data) if data else None

    def _cache_task(self, task) -> None:
        """缓存任务信息"""
        cache_key = f"{self.cache_prefix}:task:{task.task_id}"
        task_data = self._task_to_dict(task)
        self.redis_client.setex(cache_key, self.cache_ttl, json.dumps(task_data))

    def _get_cached_task(self, task_id: str) -> Optional[Dict[str, Any]]:
        """获取缓存的任务信息"""
        cache_key = f"{self.cache_prefix}:task:{task_id}"
        data = self.redis_client.get(cache_key)
        return json.loads(data) if data else None

    def _cache_expert(self, expert) -> None:
        """缓存专家信息"""
        cache_key = f"{self.cache_prefix}:expert:{expert.instance_id}"
        expert_data = self._expert_to_dict(expert)
        self.redis_client.setex(cache_key, self.cache_ttl, json.dumps(expert_data))

    def _get_cached_expert(self, instance_id: str) -> Optional[Dict[str, Any]]:
        """获取缓存的专家信息"""
        cache_key = f"{self.cache_prefix}:expert:{instance_id}"
        data = self.redis_client.get(cache_key)
        return json.loads(data) if data else None

    # === 数据转换 ===

    def _user_to_dict(self, user) -> Dict[str, Any]:
        """用户对象转字典"""
        return {
            "user_id": user.user_id,
            "username": user.username,
            "email": user.email,
            "full_name": getattr(user, 'full_name', None),
            "picture_url": getattr(user, 'picture_url', None),
            "is_active": user.is_active,
            "created_at": user.created_at.isoformat() if user.created_at else None,
            "updated_at": user.updated_at.isoformat() if user.updated_at else None
        }

    def _team_to_dict(self, team) -> Dict[str, Any]:
        """团队对象转字典"""
        return {
            "team_id": team.team_id,
            "team_name": team.team_name,
            "description": team.description,
            "owner_id": team.owner_id,
            "is_active": team.is_active,
            "max_jeff_instances": team.max_jeff_instances,
            "max_monica_instances": team.max_monica_instances,
            "max_henry_instances": team.max_henry_instances,
            "auto_scaling_enabled": team.auto_scaling_enabled,
            "jeff_scaling_enabled": team.jeff_scaling_enabled,
            "task_queue_limit": team.task_queue_limit,
            "concurrent_task_limit": team.concurrent_task_limit,
            "total_tasks_completed": team.total_tasks_completed,
            "total_content_generated": team.total_content_generated,
            "team_performance_score": team.team_performance_score,
            "created_at": team.created_at.isoformat() if team.created_at else None,
            "updated_at": team.updated_at.isoformat() if team.updated_at else None,
            "members": [self._team_member_to_dict(member) for member in team.members],
            "expert_instances": [self._expert_to_dict(expert) for expert in team.expert_instances]
        }

    def _team_member_to_dict(self, member) -> Dict[str, Any]:
        """团队成员对象转字典"""
        return {
            "id": member.id,
            "team_id": member.team_id,
            "user_id": member.user_id,
            "role": member.role,
            "permissions": member.permissions,
            "joined_at": member.joined_at.isoformat() if member.joined_at else None,
            "last_active": member.last_active.isoformat() if member.last_active else None
        }

    def _task_to_dict(self, task) -> Dict[str, Any]:
        """任务对象转字典"""
        return {
            "task_id": task.task_id,
            "team_id": task.team_id,
            "parent_task_id": task.parent_task_id,
            "title": task.title,
            "description": task.description,
            "goal": task.goal,
            "status": task.status,
            "priority": task.priority,
            "required_expert_role": task.required_expert_role,
            "target_platforms": task.target_platforms,
            "target_regions": task.target_regions,
            "content_types": task.content_types,
            "dependencies": task.dependencies,
            "subtasks": task.subtasks,
            "created_at": task.created_at.isoformat() if task.created_at else None,
            "updated_at": task.updated_at.isoformat() if task.updated_at else None,
            "due_date": task.due_date.isoformat() if task.due_date else None,
            "input_data": task.input_data,
            "output_data": task.output_data,
            "execution_log": task.execution_log,
            "error_messages": task.error_messages,
            "retry_count": task.retry_count,
            "max_retries": task.max_retries,
            "failure_reasons": task.failure_reasons,
            "last_failure_timestamp": task.last_failure_timestamp.isoformat() if task.last_failure_timestamp else None,
            "requires_replanning": task.requires_replanning,
            "metadata": task.metadata,
            "assignment": self._assignment_to_dict(task.assignment) if task.assignment else None
        }

    def _assignment_to_dict(self, assignment) -> Optional[Dict[str, Any]]:
        """任务分配对象转字典"""
        if not assignment:
            return None

        return {
            "assignment_id": assignment.assignment_id,
            "task_id": assignment.task_id,
            "expert_instance_id": assignment.expert_instance_id,
            "assigned_by": assignment.assigned_by,
            "assigned_at": assignment.assigned_at.isoformat() if assignment.assigned_at else None,
            "started_at": assignment.started_at.isoformat() if assignment.started_at else None,
            "completed_at": assignment.completed_at.isoformat() if assignment.completed_at else None,
            "estimated_duration": assignment.estimated_duration,
            "actual_duration": assignment.actual_duration
        }

    def _expert_to_dict(self, expert) -> Dict[str, Any]:
        """专家对象转字典"""
        return {
            "instance_id": expert.instance_id,
            "team_id": expert.team_id,
            "expert_role": expert.expert_role,
            "instance_name": expert.instance_name,
            "status": expert.status,
            "max_concurrent_tasks": expert.max_concurrent_tasks,
            "current_task_count": expert.current_task_count,
            "specializations": expert.specializations,
            "performance_metrics": expert.performance_metrics,
            "is_team_leader": expert.is_team_leader,
            "created_at": expert.created_at.isoformat() if expert.created_at else None,
            "last_activity": expert.last_activity.isoformat() if expert.last_activity else None
        } 
