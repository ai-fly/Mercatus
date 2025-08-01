"""
数据库连接管理
提供 PostgreSQL 异步连接池和会话管理
"""

import logging
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import NullPool
from app.config import settings

# 创建异步引擎
engine = create_async_engine(
    settings.database_url,
    echo=settings.database_echo,
    pool_size=settings.database_pool_size,
    max_overflow=settings.database_max_overflow,
    pool_timeout=settings.database_timeout,
    pool_pre_ping=True,
    pool_recycle=3600,  # 1小时回收连接
)

# 创建异步会话工厂
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

logger = logging.getLogger("Database")


async def get_database_session() -> AsyncGenerator[AsyncSession, None]:
    """
    获取数据库会话的依赖注入函数
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception as e:
            await session.rollback()
            logger.error(f"Database session error: {str(e)}")
            raise
        finally:
            await session.close()


async def init_database():
    """
    初始化数据库，创建所有表
    """
    try:
        from .models import Base
        
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        
        logger.info("Database tables created successfully")
        
    except Exception as e:
        logger.error(f"Failed to initialize database: {str(e)}")
        raise


async def close_database():
    """
    关闭数据库连接
    """
    try:
        await engine.dispose()
        logger.info("Database connections closed")
    except Exception as e:
        logger.error(f"Error closing database connections: {str(e)}")
        raise 