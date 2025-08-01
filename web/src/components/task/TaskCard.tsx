import React from 'react';
import { cn } from '@/lib/utils';
import { Card, CardContent } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Badge } from '@/components/ui/Badge';

export interface Task {
  id: string;
  title: string;
  description: string;
  status: 'pending' | 'in_progress' | 'completed' | 'failed';
  priority: 'low' | 'medium' | 'high';
  assignee?: string;
  assigneeName?: string;
  createdAt: string;
  updatedAt: string;
  dueDate?: string;
  tags: string[];
  progress: number;
}

export interface TaskCardProps {
  task: Task;
  onView?: (taskId: string) => void;
  onEdit?: (taskId: string) => void;
  onExecute?: (taskId: string) => void;
  onDelete?: (taskId: string) => void;
  className?: string;
}

const TaskCard: React.FC<TaskCardProps> = ({
  task,
  onView,
  onEdit,
  onExecute,
  onDelete,
  className,
}) => {
  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed':
        return 'success';
      case 'in_progress':
        return 'warning';
      case 'pending':
        return 'default';
      case 'failed':
        return 'danger';
      default:
        return 'default';
    }
  };

  const getStatusText = (status: string) => {
    switch (status) {
      case 'pending':
        return '待处理';
      case 'in_progress':
        return '进行中';
      case 'completed':
        return '已完成';
      case 'failed':
        return '失败';
      default:
        return status;
    }
  };

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case 'high':
        return 'danger';
      case 'medium':
        return 'warning';
      case 'low':
        return 'success';
      default:
        return 'default';
    }
  };

  const getPriorityText = (priority: string) => {
    switch (priority) {
      case 'high':
        return '高';
      case 'medium':
        return '中';
      case 'low':
        return '低';
      default:
        return priority;
    }
  };

  return (
    <Card className={cn('hover:shadow-md transition-shadow duration-200', className)}>
      <CardContent className="p-6">
        <div className="flex items-start justify-between mb-4">
          <div className="flex-1">
            <div className="flex items-center mb-2">
              <h3 className="text-lg font-medium text-gray-900 mr-2">{task.title}</h3>
              <Badge variant={getStatusColor(task.status) as any} size="sm">
                {getStatusText(task.status)}
              </Badge>
              <Badge variant={getPriorityColor(task.priority) as any} size="sm">
                {getPriorityText(task.priority)}优先级
              </Badge>
            </div>
            <p className="text-sm text-gray-600 mb-3">{task.description}</p>
            
            {/* Progress Bar */}
            <div className="mb-3">
              <div className="flex items-center justify-between text-sm mb-1">
                <span className="text-gray-500">进度</span>
                <span className="text-gray-700">{task.progress}%</span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div
                  className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                  style={{ width: `${task.progress}%` }}
                />
              </div>
            </div>

            {/* Tags */}
            {task.tags.length > 0 && (
              <div className="flex flex-wrap gap-1 mb-3">
                {task.tags.map((tag, index) => (
                  <Badge key={index} variant="info" size="sm">
                    {tag}
                  </Badge>
                ))}
              </div>
            )}

            {/* Task Info */}
            <div className="grid grid-cols-2 gap-4 text-sm text-gray-500">
              <div>
                <span className="font-medium">创建时间:</span>
                <br />
                {new Date(task.createdAt).toLocaleDateString()}
              </div>
              <div>
                <span className="font-medium">更新时间:</span>
                <br />
                {new Date(task.updatedAt).toLocaleDateString()}
              </div>
              {task.assigneeName && (
                <div>
                  <span className="font-medium">负责人:</span>
                  <br />
                  {task.assigneeName}
                </div>
              )}
              {task.dueDate && (
                <div>
                  <span className="font-medium">截止时间:</span>
                  <br />
                  {new Date(task.dueDate).toLocaleDateString()}
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Actions */}
        <div className="flex space-x-2 pt-4 border-t border-gray-200">
          {onView && (
            <Button
              variant="outline"
              size="sm"
              onClick={() => onView(task.id)}
            >
              查看详情
            </Button>
          )}
          {onEdit && (
            <Button
              variant="outline"
              size="sm"
              onClick={() => onEdit(task.id)}
            >
              编辑
            </Button>
          )}
          {onExecute && task.status === 'pending' && (
            <Button
              variant="primary"
              size="sm"
              onClick={() => onExecute(task.id)}
            >
              执行
            </Button>
          )}
          {onDelete && (
            <Button
              variant="danger"
              size="sm"
              onClick={() => onDelete(task.id)}
            >
              删除
            </Button>
          )}
        </div>
      </CardContent>
    </Card>
  );
};

export { TaskCard }; 