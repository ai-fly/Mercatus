#!/usr/bin/env python3
"""
数据库初始化脚本
用于创建 PostgreSQL 数据库表和初始数据
"""

import asyncio
import logging
import sys
import os

# 添加项目根目录到 Python 路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database.connection import engine
from app.database.models import Base
from app.config import settings

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("DatabaseInit")


async def init_database():
    """初始化数据库"""
    try:
        logger.info("开始初始化数据库...")
        
        # 创建所有表
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        
        logger.info("数据库表创建成功")
        
        # 创建初始数据（可选）
        await create_initial_data()
        
        logger.info("数据库初始化完成")
        
    except Exception as e:
        logger.error(f"数据库初始化失败: {str(e)}")
        raise


async def create_initial_data():
    """创建初始数据"""
    try:
        logger.info("创建初始数据...")
        
        # 这里可以添加一些初始数据，比如默认配置等
        # 例如：创建默认用户、默认团队配置等
        
        logger.info("初始数据创建完成")
        
    except Exception as e:
        logger.error(f"创建初始数据失败: {str(e)}")
        raise


async def drop_database():
    """删除所有表（谨慎使用）"""
    try:
        logger.warning("开始删除数据库表...")
        
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
        
        logger.info("数据库表删除成功")
        
    except Exception as e:
        logger.error(f"删除数据库表失败: {str(e)}")
        raise


async def reset_database():
    """重置数据库（删除并重新创建）"""
    try:
        logger.warning("开始重置数据库...")
        
        # 删除所有表
        await drop_database()
        
        # 重新创建所有表
        await init_database()
        
        logger.info("数据库重置完成")
        
    except Exception as e:
        logger.error(f"重置数据库失败: {str(e)}")
        raise


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="数据库初始化工具")
    parser.add_argument(
        "--action",
        choices=["init", "drop", "reset"],
        default="init",
        help="执行的操作：init(初始化), drop(删除), reset(重置)"
    )
    parser.add_argument(
        "--confirm",
        action="store_true",
        help="确认执行危险操作"
    )
    
    args = parser.parse_args()
    
    if args.action in ["drop", "reset"] and not args.confirm:
        logger.error("危险操作需要 --confirm 参数确认")
        sys.exit(1)
    
    try:
        if args.action == "init":
            asyncio.run(init_database())
        elif args.action == "drop":
            asyncio.run(drop_database())
        elif args.action == "reset":
            asyncio.run(reset_database())
            
    except Exception as e:
        logger.error(f"操作失败: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main() 