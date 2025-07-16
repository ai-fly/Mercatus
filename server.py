#!/usr/bin/env python3
"""
Mercatus Web Server
Main entry point for the Mercatus multi-agent content factory system.
"""

import logging
import sys
import os
from datetime import datetime
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import settings
from app.utils.logging import setup_logger, get_performance_logger, get_business_logger
from app.controllers.blackboard_controller import router as blackboard_router

# 设置全局日志
main_logger = setup_logger("mercatus_server", settings.log_level)
performance_logger = get_performance_logger()
business_logger = get_business_logger()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    
    # 启动阶段
    startup_time = datetime.now()
    main_logger.info(
        "🚀 Starting Mercatus Server",
        extra={
            'startup_time': startup_time.isoformat(),
            'python_version': sys.version,
            'working_directory': os.getcwd(),
            'action': 'server_startup_begin'
        }
    )
    
    try:
        # 验证配置
        await validate_configuration()
        
        # 初始化系统组件
        await initialize_system_components()
        
        startup_duration = (datetime.now() - startup_time).total_seconds()
        main_logger.info(
            "✅ Mercatus Server started successfully",
            extra={
                'startup_duration': startup_duration,
                'server_ready': True,
                'action': 'server_startup_complete'
            }
        )
        
        # 记录系统启动业务日志
        business_logger.logger.info(
            "Mercatus system started",
            extra={
                'startup_duration': startup_duration,
                'system_version': '1.0.0',
                'action': 'system_startup'
            }
        )
        
        yield
        
    except Exception as e:
        main_logger.error(
            f"❌ Failed to start Mercatus Server: {str(e)}",
            extra={
                'error_type': type(e).__name__,
                'error_message': str(e),
                'action': 'server_startup_failed'
            },
            exc_info=True
        )
        raise
    
    # 关闭阶段
    shutdown_time = datetime.now()
    main_logger.info(
        "🛑 Shutting down Mercatus Server",
        extra={
            'shutdown_time': shutdown_time.isoformat(),
            'action': 'server_shutdown_begin'
        }
    )
    
    try:
        await cleanup_system_components()
        
        shutdown_duration = (datetime.now() - shutdown_time).total_seconds()
        main_logger.info(
            "✅ Mercatus Server shutdown complete",
            extra={
                'shutdown_duration': shutdown_duration,
                'action': 'server_shutdown_complete'
            }
        )
        
    except Exception as e:
        main_logger.error(
            f"❌ Error during server shutdown: {str(e)}",
            extra={
                'error_type': type(e).__name__,
                'error_message': str(e),
                'action': 'server_shutdown_failed'
            },
            exc_info=True
        )


async def validate_configuration():
    """验证系统配置"""
    main_logger.info("🔍 Validating system configuration...")
    
    config_issues = []
    
    # 检查必需的配置
    if not settings.google_api_key:
        config_issues.append("GOOGLE_API_KEY not configured")
    
    if not settings.redis_url:
        config_issues.append("REDIS_URL not configured")
    
    # 检查数据目录
    if not os.path.exists("logs"):
        os.makedirs("logs", exist_ok=True)
        main_logger.info("📁 Created logs directory")
    
    if not os.path.exists("artifacts"):
        os.makedirs("artifacts", exist_ok=True)
        main_logger.info("📁 Created artifacts directory")
    
    # 记录配置信息
    main_logger.info(
        "📋 Configuration summary",
        extra={
            'debug_mode': settings.debug,
            'log_level': settings.log_level.value,
            'redis_url': settings.redis_url,
            'max_runtime_hours': settings.max_runtime_hours,
            'llm_temperature': settings.llm_temperature,
            'content_quality_threshold': settings.content_quality_threshold,
            'scheduler_enabled': settings.scheduler_enabled,
            'action': 'configuration_validated'
        }
    )
    
    if config_issues:
        main_logger.warning(
            f"⚠️ Configuration issues found: {'; '.join(config_issues)}",
            extra={
                'config_issues': config_issues,
                'action': 'configuration_issues'
            }
        )
    else:
        main_logger.info("✅ Configuration validation passed")


async def initialize_system_components():
    """初始化系统组件"""
    main_logger.info("🔧 Initializing system components...")
    
    with performance_logger.time_operation("system_initialization"):
        try:
            # 测试Redis连接
            from app.clients.redis_client import redis_client_instance
            redis_client = redis_client_instance.get_redis_client()
            redis_client.ping()
            main_logger.info("✅ Redis connection established")
            
        except Exception as e:
            main_logger.error(
                f"❌ Redis connection failed: {str(e)}",
                extra={
                    'redis_url': settings.redis_url,
                    'error_type': type(e).__name__,
                    'action': 'redis_connection_failed'
                },
                exc_info=True
            )
            raise
        
        try:
            # 初始化专家系统
            from app.experts.plan_expert import PlanExpert
            from app.experts.content_expert import ContentExpert
            from app.experts.rewiew_expert import ReviewExpert
            
            main_logger.info("✅ Expert classes loaded successfully")
            
        except Exception as e:
            main_logger.error(
                f"❌ Expert system initialization failed: {str(e)}",
                extra={
                    'error_type': type(e).__name__,
                    'action': 'expert_system_init_failed'
                },
                exc_info=True
            )
            raise
        
        main_logger.info("✅ System components initialized successfully")


async def cleanup_system_components():
    """清理系统组件"""
    main_logger.info("🧹 Cleaning up system components...")
    
    try:
        # 关闭Redis连接
        from app.clients.redis_client import redis_client_instance
        await redis_client_instance.close()
        main_logger.info("✅ Redis connections closed")
        
    except Exception as e:
        main_logger.error(
            f"❌ Error closing Redis connections: {str(e)}",
            extra={'error_type': type(e).__name__, 'action': 'redis_cleanup_failed'},
            exc_info=True
        )
    
    main_logger.info("✅ System cleanup completed")


# 创建FastAPI应用
app = FastAPI(
    title="Mercatus - Multi-Agent Content Factory",
    description="Intelligent content generation system with multi-agent collaboration",
    version="1.0.0",
    lifespan=lifespan
)

# 添加CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 在生产环境中应该限制为特定域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(blackboard_router)

# 根路径
@app.get("/")
async def root():
    """系统根路径 - 健康检查"""
    return {
        "message": "Mercatus Multi-Agent Content Factory",
        "version": "1.0.0",
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "endpoints": {
            "health": "/health",
            "api": "/api/v1",
            "docs": "/docs"
        }
    }

# 健康检查端点
@app.get("/health")
async def health_check():
    """详细的健康检查"""
    health_status = {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0",
        "components": {}
    }
    
    try:
        # 检查Redis连接
        from app.clients.redis_client import redis_client_instance
        redis_client = redis_client_instance.get_redis_client()
        await redis_client.ping()
        health_status["components"]["redis"] = "healthy"
        
    except Exception as e:
        health_status["components"]["redis"] = f"unhealthy: {str(e)}"
        health_status["status"] = "degraded"
        
        main_logger.warning(
            "Redis health check failed",
            extra={
                'error_message': str(e),
                'action': 'health_check_redis_failed'
            }
        )
    
    # 记录健康检查
    main_logger.debug(
        "Health check performed",
        extra={
            'health_status': health_status["status"],
            'action': 'health_check'
        }
    )
    
    return health_status

# 全局异常处理器
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """全局异常处理"""
    main_logger.error(
        f"Unhandled exception: {str(exc)}",
        extra={
            'request_url': str(request.url),
            'request_method': request.method,
            'error_type': type(exc).__name__,
            'action': 'unhandled_exception'
        },
        exc_info=True
    )
    
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "message": "An unexpected error occurred",
            "timestamp": datetime.now().isoformat()
        }
    )


if __name__ == "__main__":
    # 命令行启动
    main_logger.info(
        "🎯 Starting Mercatus server from command line",
        extra={
            'host': '0.0.0.0',
            'port': 8000,
            'debug': settings.debug,
            'action': 'cli_startup'
        }
    )
    
    uvicorn.run(
        "server:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug,
        log_level=settings.log_level.value.lower(),
        access_log=True
    )