#!/usr/bin/env python3
"""
Mercatus Web Server
Main entry point for the Mercatus multi-agent content factory system.
"""

import asyncio
import logging
import sys
import os
from datetime import datetime
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import settings
from app.utils.logging import setup_logger
from app.controllers.blackboard_controller import router as blackboard_router
from app.controllers.auth_controller import router as auth_router
from app.core.team_manager import TeamManager
from app.services.hybrid_storage import HybridStorageService
from app.database.connection import init_database, get_database_session, AsyncSessionLocal
from app.clients.redis_client import redis_client_instance
from app.dependencies import set_global_services

# 设置全局日志
setup_logger()
logger = logging.getLogger("Server")

# 全局变量
team_manager: TeamManager = None
hybrid_storage_service: HybridStorageService = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    global team_manager, hybrid_storage_service
    
    # 启动时初始化
    logger.info("Starting Mercatus server...")
    
    try:
        # Redis 连接已在构造函数中初始化
        logger.info("Redis connection ready")
        
        # 初始化数据库
        await init_database()
        logger.info("Database initialized")
        
        # 初始化混合存储服务
        hybrid_storage_service = HybridStorageService()
        logger.info("Hybrid storage service initialized")
        
        # 初始化团队管理器
        team_manager = TeamManager(hybrid_storage_service)
        logger.info("Team manager initialized")
        
        # 设置全局服务实例
        set_global_services(team_manager, hybrid_storage_service)
        
        logger.info("Mercatus server started successfully")
        
    except Exception as e:
        logger.error(f"Failed to start server: {str(e)}")
        raise
    
    yield
    
    # 关闭时清理
    logger.info("Shutting down Mercatus server...")
    
    try:
        # 关闭 Redis 连接
        redis_client_instance.close()
        logger.info("Redis connection closed")
        
        logger.info("Mercatus server shutdown completed")
        
    except Exception as e:
        logger.error(f"Error during shutdown: {str(e)}")


# 创建 FastAPI 应用
app = FastAPI(
    title="Mercatus Content Factory API",
    description="Multi-tenant team collaboration and content generation platform",
    version="1.0.0",
    lifespan=lifespan
)

# 添加 CORS 中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 在生产环境中应该限制具体域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


async def get_database_session_dep():
    """获取数据库会话依赖"""
    async with get_database_session() as session:
        yield session


# 注册路由
app.include_router(
    blackboard_router,
    prefix="/api/v1"
)

app.include_router(
    auth_router,
    prefix="/api/v1"
)


# 健康检查端点
@app.get("/health")
async def health_check():
    """健康检查端点"""
    return {
        "status": "healthy",
        "service": "Mercatus Content Factory",
        "version": "1.0.0",
        "database": "connected" if hybrid_storage_service else "disconnected",
        "redis": "connected" if redis_client_instance.is_connected() else "disconnected"
    }


# 根端点
@app.get("/")
async def root():
    """根端点"""
    return {
        "message": "Welcome to Mercatus Content Factory API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health"
    }


# 全局异常处理器
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """全局异常处理器"""
    logger.error(
        f"Unhandled exception: {str(exc)}",
        extra={
            'path': request.url.path,
            'method': request.method,
            'error': str(exc)
        },
        exc_info=True
    )
    
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "message": "An unexpected error occurred",
            "detail": str(exc) if settings.debug else "Please try again later"
        }
    )


if __name__ == "__main__":
    # 启动服务器
    uvicorn.run(
        "server:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level="info" if not settings.debug else "debug"
    )