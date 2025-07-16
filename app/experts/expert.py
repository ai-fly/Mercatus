import logging
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Dict, Any
from pydantic import BaseModel

from app.utils.logging import get_business_logger, get_performance_logger


class ExpertTask(BaseModel):
    task_name: str
    task_description: str
    task_goal: str


class ExpertBase(ABC):
    def __init__(self, name: str, description: str, index: int = 1):
        self.name = name
        self.description = description
        self.index = index
        self.retries = 3
        self.trust_score = 80.0
        
        # 设置日志器
        self.logger = logging.getLogger(f"{self.__class__.__name__}-{index}")
        self.business_logger = get_business_logger()
        self.performance_logger = get_performance_logger()
        
        # 初始化代理
        self.create_agents()
        
        # 统计信息
        self.total_tasks = 0
        self.successful_tasks = 0
        self.failed_tasks = 0
        
        self.logger.info(
            f"Expert {self.name} initialized",
            extra={
                'expert_name': self.name,
                'expert_type': self.__class__.__name__,
                'index': index,
                'retries': self.retries,
                'trust_score': self.trust_score,
                'action': 'expert_initialized'
            }
        )

    @abstractmethod
    async def run(self, task: ExpertTask) -> Dict[str, Any]:
        """Execute the expert task"""
        pass

    @abstractmethod
    def create_agents(self) -> None:
        """Initialize agent instances"""
        pass

    async def execute_with_monitoring(self, task: ExpertTask) -> Dict[str, Any]:
        """Execute task with comprehensive monitoring and logging"""
        
        task_start_time = datetime.now()
        
        self.logger.info(
            f"Starting task execution: {task.task_name}",
            extra={
                'expert_name': self.name,
                'expert_type': self.__class__.__name__,
                'task_name': task.task_name,
                'task_goal': task.task_goal,
                'action': 'task_start'
            }
        )
        
        self.total_tasks += 1
        
        try:
            with self.performance_logger.time_operation(
                f"{self.__class__.__name__}_task_execution",
                expert_name=self.name,
                task_name=task.task_name
            ):
                result = await self.run(task)
                
                execution_time = (datetime.now() - task_start_time).total_seconds()
                
                # 检查结果状态
                result_status = "unknown"
                if isinstance(result, dict):
                    result_status = result.get('status', 'unknown')
                
                if result_status in ['completed', 'success']:
                    self.successful_tasks += 1
                    self.trust_score = min(100.0, self.trust_score + 0.5)
                    
                    self.logger.info(
                        f"Task completed successfully: {task.task_name}",
                        extra={
                            'expert_name': self.name,
                            'expert_type': self.__class__.__name__,
                            'task_name': task.task_name,
                            'execution_time': execution_time,
                            'result_status': result_status,
                            'new_trust_score': self.trust_score,
                            'action': 'task_success'
                        }
                    )
                    
                elif result_status in ['failed', 'error']:
                    self.failed_tasks += 1
                    self.trust_score = max(0.0, self.trust_score - 2.0)
                    
                    self.logger.warning(
                        f"Task failed: {task.task_name}",
                        extra={
                            'expert_name': self.name,
                            'expert_type': self.__class__.__name__,
                            'task_name': task.task_name,
                            'execution_time': execution_time,
                            'result_status': result_status,
                            'new_trust_score': self.trust_score,
                            'action': 'task_failed'
                        }
                    )
                
                # 记录性能指标
                success_rate = self.successful_tasks / self.total_tasks if self.total_tasks > 0 else 0
                self.business_logger.log_expert_performance(
                    self.__class__.__name__, 
                    self.total_tasks, 
                    execution_time, 
                    success_rate
                )
                
                return result
                
        except Exception as e:
            execution_time = (datetime.now() - task_start_time).total_seconds()
            self.failed_tasks += 1
            self.trust_score = max(0.0, self.trust_score - 5.0)
            
            self.logger.error(
                f"Task execution failed with exception: {task.task_name}",
                extra={
                    'expert_name': self.name,
                    'expert_type': self.__class__.__name__,
                    'task_name': task.task_name,
                    'execution_time': execution_time,
                    'error_type': type(e).__name__,
                    'error_message': str(e),
                    'new_trust_score': self.trust_score,
                    'action': 'task_exception'
                },
                exc_info=True
            )
            
            return {
                "status": "error",
                "error_type": type(e).__name__,
                "error_message": str(e),
                "execution_time": execution_time
            }

    def get_performance_stats(self) -> Dict[str, Any]:
        """Get expert performance statistics"""
        success_rate = self.successful_tasks / self.total_tasks if self.total_tasks > 0 else 0
        
        stats = {
            "expert_name": self.name,
            "expert_type": self.__class__.__name__,
            "total_tasks": self.total_tasks,
            "successful_tasks": self.successful_tasks,
            "failed_tasks": self.failed_tasks,
            "success_rate": success_rate,
            "trust_score": self.trust_score
        }
        
        self.logger.debug(
            f"Performance stats for {self.name}",
            extra={**stats, 'action': 'performance_stats_requested'}
        )
        
        return stats

    def get_name(self):
        return self.name

    def get_description(self):
        return self.description


