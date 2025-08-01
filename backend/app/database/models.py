"""
数据库模型定义
定义 PostgreSQL 数据库表结构和关系
"""

import json
from datetime import datetime
from typing import Dict, List, Any, Optional
from sqlalchemy import (
    Column, String, Integer, Boolean, DateTime, Text, JSON, 
    ForeignKey, Float, Index, UniqueConstraint
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID, ARRAY
import uuid

Base = declarative_base()


class User(Base):
    """用户表"""
    __tablename__ = "users"
    
    user_id = Column(String(50), primary_key=True, index=True)
    username = Column(String(100), unique=False, nullable=True, index=True)  # 用户名可选，仅用于展示
    email = Column(String(255), unique=True, nullable=False, index=True)  # 邮箱唯一且必填，OAuth登录主键
    full_name = Column(String(255), nullable=True)
    picture_url = Column(String(2048), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关系
    owned_teams = relationship("Team", back_populates="owner", foreign_keys="Team.owner_id")
    team_memberships = relationship("TeamMember", back_populates="user")
    
    __table_args__ = (
        Index('idx_users_created_at', 'created_at'),
        UniqueConstraint('email', name='uq_users_email'),
    )


class Team(Base):
    """团队表"""
    __tablename__ = "teams"
    
    team_id = Column(String(50), primary_key=True, index=True)
    team_name = Column(String(200), nullable=False, unique=True)
    description = Column(Text, nullable=True)  # 添加 description 字段
    owner_id = Column(String(50), ForeignKey("users.user_id"), nullable=False)
    is_active = Column(Boolean, default=True)
    
    # 团队配置
    max_jeff_instances = Column(Integer, default=1)
    max_monica_instances = Column(Integer, default=3)
    max_henry_instances = Column(Integer, default=2)
    auto_scaling_enabled = Column(Boolean, default=True)
    jeff_scaling_enabled = Column(Boolean, default=False)
    task_queue_limit = Column(Integer, default=100)
    concurrent_task_limit = Column(Integer, default=10)
    
    # 性能指标
    total_tasks_completed = Column(Integer, default=0)
    total_content_generated = Column(Integer, default=0)
    team_performance_score = Column(Float, default=0.0)
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关系
    owner = relationship("User", back_populates="owned_teams", foreign_keys=[owner_id])
    members = relationship("TeamMember", back_populates="team", cascade="all, delete-orphan")
    expert_instances = relationship("ExpertInstance", back_populates="team", cascade="all, delete-orphan")
    tasks = relationship("BlackboardTask", back_populates="team", cascade="all, delete-orphan")
    
    __table_args__ = (
        Index('idx_teams_owner', 'owner_id'),
        Index('idx_teams_created_at', 'created_at'),
    )


class TeamMember(Base):
    """团队成员表"""
    __tablename__ = "team_members"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    team_id = Column(String(50), ForeignKey("teams.team_id"), nullable=False)
    user_id = Column(String(50), ForeignKey("users.user_id"), nullable=False)
    role = Column(String(20), nullable=False)  # owner, admin, member, observer
    permissions = Column(ARRAY(String), default=[])
    joined_at = Column(DateTime, default=datetime.utcnow)
    last_active = Column(DateTime, default=datetime.utcnow)
    
    # 关系
    team = relationship("Team", back_populates="members")
    user = relationship("User", back_populates="team_memberships")
    
    __table_args__ = (
        Index('idx_team_members_team', 'team_id'),
        Index('idx_team_members_user', 'user_id'),
        UniqueConstraint('team_id', 'user_id', name='uq_team_member'),
    )


class ExpertInstance(Base):
    """专家实例表"""
    __tablename__ = "expert_instances"
    
    instance_id = Column(String(50), primary_key=True, index=True)
    team_id = Column(String(50), ForeignKey("teams.team_id"), nullable=False)
    expert_role = Column(String(20), nullable=False)  # planner, executor, evaluator
    instance_name = Column(String(200), nullable=False)
    status = Column(String(20), default="active")  # active, busy, offline
    max_concurrent_tasks = Column(Integer, default=3)
    current_task_count = Column(Integer, default=0)
    specializations = Column(ARRAY(String), default=[])
    performance_metrics = Column(JSON, default=dict)
    is_team_leader = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_activity = Column(DateTime, default=datetime.utcnow)
    
    # 关系
    team = relationship("Team", back_populates="expert_instances")
    task_assignments = relationship("TaskAssignment", back_populates="expert_instance")
    
    __table_args__ = (
        Index('idx_expert_instances_team', 'team_id'),
        Index('idx_expert_instances_role', 'expert_role'),
        Index('idx_expert_instances_status', 'status'),
    )


class BlackboardTask(Base):
    """BlackBoard 任务表"""
    __tablename__ = "blackboard_tasks"
    
    task_id = Column(String(50), primary_key=True, index=True)
    team_id = Column(String(50), ForeignKey("teams.team_id"), nullable=False)
    parent_task_id = Column(String(50), nullable=True)
    
    # 任务基本信息
    title = Column(String(500), nullable=False)
    description = Column(Text, nullable=False)
    goal = Column(Text, nullable=False)
    status = Column(String(20), default="pending")  # pending, assigned, in_progress, completed, failed, cancelled
    priority = Column(String(20), default="medium")  # low, medium, high, urgent
    required_expert_role = Column(String(20), nullable=False)
    
    # 平台和内容特定
    target_platforms = Column(ARRAY(String), default=[])
    target_regions = Column(ARRAY(String), default=[])
    content_types = Column(ARRAY(String), default=[])
    
    # 依赖关系
    dependencies = Column(JSON, default=list)
    subtasks = Column(ARRAY(String), default=[])
    
    # 时间管理
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    due_date = Column(DateTime, nullable=True)
    
    # 结果和输出
    input_data = Column(JSON, default=dict)
    output_data = Column(JSON, default=dict)
    execution_log = Column(ARRAY(String), default=[])
    error_messages = Column(ARRAY(String), default=[])
    
    # 重试和失败处理
    retry_count = Column(Integer, default=0)
    max_retries = Column(Integer, default=3)
    failure_reasons = Column(ARRAY(String), default=[])
    last_failure_timestamp = Column(DateTime, nullable=True)
    requires_replanning = Column(Boolean, default=False)
    
    # 元数据
    task_metadata = Column(JSON, default=dict)
    
    # 关系
    team = relationship("Team", back_populates="tasks")
    assignment = relationship("TaskAssignment", back_populates="task", uselist=False)
    events = relationship("TaskEvent", back_populates="task", cascade="all, delete-orphan")
    
    __table_args__ = (
        Index('idx_tasks_team', 'team_id'),
        Index('idx_tasks_status', 'status'),
        Index('idx_tasks_priority', 'priority'),
        Index('idx_tasks_expert_role', 'required_expert_role'),
        Index('idx_tasks_created_at', 'created_at'),
        Index('idx_tasks_due_date', 'due_date'),
    )


class TaskAssignment(Base):
    """任务分配表"""
    __tablename__ = "task_assignments"
    
    assignment_id = Column(String(50), primary_key=True, index=True)
    task_id = Column(String(50), ForeignKey("blackboard_tasks.task_id"), nullable=False, unique=True)
    expert_instance_id = Column(String(50), ForeignKey("expert_instances.instance_id"), nullable=False)
    assigned_by = Column(String(50), nullable=False)
    assigned_at = Column(DateTime, default=datetime.utcnow)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    estimated_duration = Column(Integer, nullable=True)  # 分钟
    actual_duration = Column(Integer, nullable=True)  # 分钟
    
    # 关系
    task = relationship("BlackboardTask", back_populates="assignment")
    expert_instance = relationship("ExpertInstance", back_populates="task_assignments")
    
    __table_args__ = (
        Index('idx_task_assignments_task', 'task_id'),
        Index('idx_task_assignments_expert', 'expert_instance_id'),
        Index('idx_task_assignments_assigned_at', 'assigned_at'),
    )


class TaskEvent(Base):
    """任务事件表"""
    __tablename__ = "task_events"
    
    event_id = Column(String(50), primary_key=True, index=True)
    task_id = Column(String(50), ForeignKey("blackboard_tasks.task_id"), nullable=False)
    event_type = Column(String(50), nullable=False)  # created, assigned, started, completed, failed
    event_data = Column(JSON, default=dict)
    triggered_by = Column(String(50), nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    # 关系
    task = relationship("BlackboardTask", back_populates="events")
    
    __table_args__ = (
        Index('idx_task_events_task', 'task_id'),
        Index('idx_task_events_type', 'event_type'),
        Index('idx_task_events_timestamp', 'timestamp'),
    ) 