import logging
import logging.handlers
import os
import sys
import json
from datetime import datetime
from typing import Dict, Any, Optional
from contextlib import contextmanager

class StructuredFormatter(logging.Formatter):
    """结构化日志格式器"""
    
    def format(self, record):
        # 基础日志信息
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno
        }
        
        # 添加上下文信息
        if hasattr(record, 'user_id'):
            log_data['user_id'] = record.user_id
        if hasattr(record, 'team_id'):
            log_data['team_id'] = record.team_id
        if hasattr(record, 'task_id'):
            log_data['task_id'] = record.task_id
        if hasattr(record, 'request_id'):
            log_data['request_id'] = record.request_id
        if hasattr(record, 'execution_time'):
            log_data['execution_time'] = record.execution_time
        if hasattr(record, 'expert_type'):
            log_data['expert_type'] = record.expert_type
            
        # 添加异常信息
        if record.exc_info:
            log_data['exception'] = self.formatException(record.exc_info)
            
        return json.dumps(log_data, ensure_ascii=False)

class BusinessLogger:
    """业务日志记录器"""
    
    def __init__(self, name: str):
        self.logger = logging.getLogger(name)
    
    def log_task_created(self, task_id: str, title: str, team_id: str, creator_id: str, priority: str):
        """记录任务创建"""
        self.logger.info(
            f"Task created: {title}",
            extra={
                'task_id': task_id,
                'team_id': team_id,
                'user_id': creator_id,
                'action': 'task_created',
                'priority': priority
            }
        )
    
    def log_task_assigned(self, task_id: str, expert_instance_id: str, team_id: str, assigned_by: str):
        """记录任务分配"""
        self.logger.info(
            f"Task assigned to expert {expert_instance_id}",
            extra={
                'task_id': task_id,
                'team_id': team_id,
                'expert_instance_id': expert_instance_id,
                'user_id': assigned_by,
                'action': 'task_assigned'
            }
        )
    
    def log_task_execution_start(self, task_id: str, expert_type: str, team_id: str):
        """记录任务执行开始"""
        self.logger.info(
            f"Task execution started by {expert_type}",
            extra={
                'task_id': task_id,
                'team_id': team_id,
                'expert_type': expert_type,
                'action': 'task_execution_start'
            }
        )
    
    def log_task_execution_complete(self, task_id: str, expert_type: str, execution_time: float, team_id: str):
        """记录任务执行完成"""
        self.logger.info(
            f"Task execution completed by {expert_type}",
            extra={
                'task_id': task_id,
                'team_id': team_id,
                'expert_type': expert_type,
                'execution_time': execution_time,
                'action': 'task_execution_complete'
            }
        )
    
    def log_expert_performance(self, expert_type: str, task_count: int, avg_execution_time: float, success_rate: float):
        """记录专家性能指标"""
        self.logger.info(
            f"Expert performance metrics",
            extra={
                'expert_type': expert_type,
                'task_count': task_count,
                'avg_execution_time': avg_execution_time,
                'success_rate': success_rate,
                'action': 'performance_metrics'
            }
        )

class PerformanceLogger:
    """性能日志记录器"""
    
    def __init__(self, name: str):
        self.logger = logging.getLogger(name)
    
    @contextmanager
    def time_operation(self, operation_name: str, **context):
        """记录操作执行时间"""
        start_time = datetime.now()
        self.logger.debug(
            f"Starting {operation_name}",
            extra={**context, 'action': 'operation_start', 'operation': operation_name}
        )
        
        try:
            yield
            execution_time = (datetime.now() - start_time).total_seconds()
            self.logger.info(
                f"Completed {operation_name}",
                extra={
                    **context,
                    'action': 'operation_complete',
                    'operation': operation_name,
                    'execution_time': execution_time
                }
            )
        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            self.logger.error(
                f"Failed {operation_name}: {str(e)}",
                extra={
                    **context,
                    'action': 'operation_failed',
                    'operation': operation_name,
                    'execution_time': execution_time,
                    'error': str(e)
                },
                exc_info=True
            )
            raise

def setup_logger(name="mercatus", log_level=logging.INFO, use_structured_logging=True):
    """
    Set up and configure application logging with enhanced features
    """
    # Suppress specific warnings
    logging.getLogger("langchain_google_genai._function_utils").setLevel(logging.ERROR)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    
    # Create log directory
    log_dir = "backend/logs"
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    # Create log filename with date
    today = datetime.now().strftime("%Y-%m-%d")
    log_file = f"{log_dir}/{name}_{today}.log"
    error_log_file = f"{log_dir}/{name}_error_{today}.log"
    performance_log_file = f"{log_dir}/{name}_performance_{today}.log"
    
    # Configure log formatters
    if use_structured_logging:
        formatter = StructuredFormatter()
    else:
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
    
    # Handle LogLevel enum - extract string value if needed
    if hasattr(log_level, 'value'):
        log_level = log_level.value
    
    # Create logger
    logger = logging.getLogger(name)
    logger.setLevel(log_level)
    
    # Clear existing handlers
    if logger.handlers:
        logger.handlers.clear()
    
    # Add rotating file handler for general logs
    file_handler = logging.handlers.RotatingFileHandler(
        log_file, maxBytes=100*1024*1024, backupCount=5
    )
    file_handler.setFormatter(formatter)
    file_handler.setLevel(logging.DEBUG)
    logger.addHandler(file_handler)
    
    # Add separate handler for error logs
    error_handler = logging.handlers.RotatingFileHandler(
        error_log_file, maxBytes=50*1024*1024, backupCount=3
    )
    error_handler.setFormatter(formatter)
    error_handler.setLevel(logging.ERROR)
    logger.addHandler(error_handler)
    
    # Add performance log handler
    performance_handler = logging.handlers.RotatingFileHandler(
        performance_log_file, maxBytes=50*1024*1024, backupCount=3
    )
    performance_handler.setFormatter(formatter)
    performance_handler.addFilter(lambda record: getattr(record, 'action', '') in [
        'operation_complete', 'operation_failed', 'performance_metrics'
    ])
    logger.addHandler(performance_handler)
    
    # Add console handler with different formatting
    console_handler = logging.StreamHandler(sys.stdout)
    if use_structured_logging:
        # Use simpler format for console
        console_formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        console_handler.setFormatter(console_formatter)
    else:
        console_handler.setFormatter(formatter)
    
    console_handler.setLevel(logging.INFO)
    logger.addHandler(console_handler)
    
    logger.propagate = False
    
    # Log system startup
    logger.info(f"Logger initialized for {name} with level {log_level}")
    
    return logger

# 全局日志器实例
business_logger = BusinessLogger("mercatus.business")
performance_logger = PerformanceLogger("mercatus.performance")

# 导出便捷函数
def get_business_logger() -> BusinessLogger:
    return business_logger

def get_performance_logger() -> PerformanceLogger:
    return performance_logger
