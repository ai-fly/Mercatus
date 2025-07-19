"""
数据库仓库层
提供数据访问抽象和业务逻辑封装
"""

import logging
from typing import List, Optional, Dict, Any
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, and_, or_
from sqlalchemy.orm import selectinload, joinedload

from .models import (
    User, Team, TeamMember, BlackboardTask, ExpertInstance, 
    TaskAssignment, TaskEvent
)
from app.types.blackboard import (
    TaskStatus, TaskPriority, ExpertRole, TeamRole
)

logger = logging.getLogger("DatabaseRepositories")


class UserRepository:
    """用户数据仓库"""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def create_user(self, user_id: str, username: str, email: str = None, organization_id: str = None) -> User:
        """创建用户"""
        user = User(
            user_id=user_id,
            username=username,
            email=email,
            organization_id=organization_id
        )
        self.session.add(user)
        await self.session.flush()
        return user
    
    async def get_user_by_id(self, user_id: str) -> Optional[User]:
        """根据ID获取用户"""
        result = await self.session.execute(
            select(User).where(User.user_id == user_id)
        )
        return result.scalar_one_or_none()
    
    async def get_user_by_username(self, username: str) -> Optional[User]:
        """根据用户名获取用户"""
        result = await self.session.execute(
            select(User).where(User.username == username)
        )
        return result.scalar_one_or_none()
    
    async def get_user_by_email(self, email: str) -> Optional[User]:
        """根据邮箱获取用户"""
        result = await self.session.execute(
            select(User).where(User.email == email)
        )
        return result.scalar_one_or_none()
    
    async def get_user_teams(self, user_id: str) -> List[Team]:
        """获取用户的所有团队"""
        result = await self.session.execute(
            select(Team).options(
                selectinload(Team.members),
                selectinload(Team.expert_instances)
            ).where(
                or_(
                    Team.owner_id == user_id,
                    Team.members.any(TeamMember.user_id == user_id)
                )
            )
        )
        return result.scalars().all()


class TeamRepository:
    """团队数据仓库"""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def create_team(self, team_data: Dict[str, Any]) -> Team:
        """创建团队"""
        team = Team(**team_data)
        self.session.add(team)
        await self.session.flush()
        return team
    
    async def get_team_by_id(self, team_id: str) -> Optional[Team]:
        """根据ID获取团队"""
        result = await self.session.execute(
            select(Team).options(
                selectinload(Team.members),
                selectinload(Team.expert_instances),
                selectinload(Team.owner)
            ).where(Team.team_id == team_id)
        )
        return result.scalar_one_or_none()
    
    async def get_teams_by_organization(self, organization_id: str) -> List[Team]:
        """获取组织的所有团队"""
        result = await self.session.execute(
            select(Team).options(
                selectinload(Team.members),
                selectinload(Team.expert_instances)
            ).where(Team.organization_id == organization_id)
        )
        return result.scalars().all()
    
    async def update_team(self, team_id: str, update_data: Dict[str, Any]) -> Optional[Team]:
        """更新团队"""
        result = await self.session.execute(
            update(Team)
            .where(Team.team_id == team_id)
            .values(**update_data, updated_at=datetime.utcnow())
        )
        await self.session.flush()
        return await self.get_team_by_id(team_id)
    
    async def add_team_member(self, team_id: str, user_id: str, role: str = "member") -> TeamMember:
        """添加团队成员"""
        member = TeamMember(
            team_id=team_id,
            user_id=user_id,
            role=role
        )
        self.session.add(member)
        await self.session.flush()
        return member


class TaskRepository:
    """任务数据仓库"""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def create_task(self, task_data: Dict[str, Any]) -> BlackboardTask:
        """创建任务"""
        task = BlackboardTask(**task_data)
        self.session.add(task)
        await self.session.flush()
        return task
    
    async def get_task_by_id(self, task_id: str) -> Optional[BlackboardTask]:
        """根据ID获取任务"""
        result = await self.session.execute(
            select(BlackboardTask).options(
                selectinload(BlackboardTask.assignment),
                selectinload(BlackboardTask.events),
                selectinload(BlackboardTask.team)
            ).where(BlackboardTask.task_id == task_id)
        )
        return result.scalar_one_or_none()
    
    async def get_team_tasks(self, team_id: str, status: Optional[str] = None) -> List[BlackboardTask]:
        """获取团队任务"""
        query = select(BlackboardTask).options(
            selectinload(BlackboardTask.assignment),
            selectinload(BlackboardTask.events)
        ).where(BlackboardTask.team_id == team_id)
        
        if status:
            query = query.where(BlackboardTask.status == status)
        
        result = await self.session.execute(query)
        return result.scalars().all()
    
    async def update_task_status(self, task_id: str, status: str, **kwargs) -> Optional[BlackboardTask]:
        """更新任务状态"""
        update_data = {"status": status, "updated_at": datetime.utcnow(), **kwargs}
        result = await self.session.execute(
            update(BlackboardTask)
            .where(BlackboardTask.task_id == task_id)
            .values(**update_data)
        )
        await self.session.flush()
        return await self.get_task_by_id(task_id)
    
    async def create_task_event(self, event_data: Dict[str, Any]) -> TaskEvent:
        """创建任务事件"""
        event = TaskEvent(**event_data)
        self.session.add(event)
        await self.session.flush()
        return event


class ExpertInstanceRepository:
    """专家实例数据仓库"""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def create_expert_instance(self, expert_data: Dict[str, Any]) -> ExpertInstance:
        """创建专家实例"""
        expert = ExpertInstance(**expert_data)
        self.session.add(expert)
        await self.session.flush()
        return expert
    
    async def get_expert_by_id(self, instance_id: str) -> Optional[ExpertInstance]:
        """根据ID获取专家实例"""
        result = await self.session.execute(
            select(ExpertInstance).where(ExpertInstance.instance_id == instance_id)
        )
        return result.scalar_one_or_none()
    
    async def get_team_experts(self, team_id: str, role: Optional[str] = None) -> List[ExpertInstance]:
        """获取团队专家实例"""
        query = select(ExpertInstance).where(ExpertInstance.team_id == team_id)
        if role:
            query = query.where(ExpertInstance.expert_role == role)
        
        result = await self.session.execute(query)
        return result.scalars().all()
    
    async def update_expert_status(self, instance_id: str, status: str, **kwargs) -> Optional[ExpertInstance]:
        """更新专家状态"""
        update_data = {"status": status, "last_activity": datetime.utcnow(), **kwargs}
        result = await self.session.execute(
            update(ExpertInstance)
            .where(ExpertInstance.instance_id == instance_id)
            .values(**update_data)
        )
        await self.session.flush()
        return await self.get_expert_by_id(instance_id)


class TaskAssignmentRepository:
    """任务分配数据仓库"""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def create_assignment(self, assignment_data: Dict[str, Any]) -> TaskAssignment:
        """创建任务分配"""
        assignment = TaskAssignment(**assignment_data)
        self.session.add(assignment)
        await self.session.flush()
        return assignment
    
    async def get_assignment_by_task_id(self, task_id: str) -> Optional[TaskAssignment]:
        """根据任务ID获取分配"""
        result = await self.session.execute(
            select(TaskAssignment).options(
                selectinload(TaskAssignment.expert_instance)
            ).where(TaskAssignment.task_id == task_id)
        )
        return result.scalar_one_or_none()
    
    async def update_assignment(self, assignment_id: str, update_data: Dict[str, Any]) -> Optional[TaskAssignment]:
        """更新任务分配"""
        result = await self.session.execute(
            update(TaskAssignment)
            .where(TaskAssignment.assignment_id == assignment_id)
            .values(**update_data)
        )
        await self.session.flush()
        return result.scalar_one_or_none() 