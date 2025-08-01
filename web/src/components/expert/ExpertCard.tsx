import React from 'react';
import { cn } from '@/lib/utils';
import { Card, CardContent } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';

export interface Expert {
  id: string;
  name: string;
  type: string;
  description: string;
  status: 'active' | 'idle' | 'busy' | 'error' | 'offline';
  currentTask?: {
    id: string;
    title: string;
    progress: number;
  };
  performance: {
    successRate: number;
    totalTasks: number;
    completedTasks: number;
    averageCompletionTime: number;
    lastActive: string;
  };
  capabilities: string[];
}

export interface ExpertCardProps {
  expert: Expert;
  onView?: (expertId: string) => void;
  onConfigure?: (expertId: string) => void;
  className?: string;
}

const ExpertCard: React.FC<ExpertCardProps> = ({
  expert,
  onView,
  onConfigure,
  className,
}) => {
  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active':
        return 'success';
      case 'busy':
        return 'warning';
      case 'idle':
        return 'info';
      case 'error':
        return 'danger';
      case 'offline':
        return 'default';
      default:
        return 'default';
    }
  };

  const getStatusText = (status: string) => {
    switch (status) {
      case 'active':
        return '活跃';
      case 'busy':
        return '忙碌';
      case 'idle':
        return '空闲';
      case 'error':
        return '错误';
      case 'offline':
        return '离线';
      default:
        return status;
    }
  };

  const getExpertIcon = (type: string) => {
    switch (type.toLowerCase()) {
      case 'writer':
        return (
          <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
          </svg>
        );
      case 'designer':
        return (
          <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 21a4 4 0 01-4-4V5a2 2 0 012-2h4a2 2 0 012 2v12a4 4 0 01-4 4zM21 5a2 2 0 00-2-2h-4a2 2 0 00-2 2v12a4 4 0 004 4h4a2 2 0 002-2V5z" />
          </svg>
        );
      case 'analyst':
        return (
          <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
          </svg>
        );
      default:
        return (
          <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
          </svg>
        );
    }
  };

  const formatTime = (minutes: number) => {
    if (minutes < 60) {
      return `${minutes}分钟`;
    }
    const hours = Math.floor(minutes / 60);
    const remainingMinutes = minutes % 60;
    return `${hours}小时${remainingMinutes}分钟`;
  };

  return (
    <Card className={cn('hover:shadow-md transition-shadow duration-200', className)}>
      <CardContent className="p-6">
        {/* Header */}
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <div className="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center">
                {getExpertIcon(expert.type)}
              </div>
            </div>
            <div className="ml-3">
              <h3 className="text-lg font-medium text-gray-900">{expert.name}</h3>
              <p className="text-sm text-gray-500">{expert.type}</p>
            </div>
          </div>
          <Badge variant={getStatusColor(expert.status) as any} size="md">
            {getStatusText(expert.status)}
          </Badge>
        </div>

        {/* Description */}
        <p className="text-sm text-gray-600 mb-4">{expert.description}</p>

        {/* Current Task */}
        {expert.currentTask && (
          <div className="mb-4 p-3 bg-blue-50 rounded-lg">
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm font-medium text-blue-900">当前任务</span>
              <span className="text-xs text-blue-600">{expert.currentTask.progress}%</span>
            </div>
            <p className="text-sm text-blue-800 mb-2">{expert.currentTask.title}</p>
            <div className="w-full bg-blue-200 rounded-full h-2">
              <div
                className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                style={{ width: `${expert.currentTask.progress}%` }}
              />
            </div>
          </div>
        )}

        {/* Performance Metrics */}
        <div className="grid grid-cols-2 gap-4 mb-4">
          <div className="text-center p-3 bg-gray-50 rounded-lg">
            <div className="text-2xl font-bold text-blue-600">{expert.performance.successRate}%</div>
            <div className="text-xs text-gray-500">成功率</div>
          </div>
          <div className="text-center p-3 bg-gray-50 rounded-lg">
            <div className="text-2xl font-bold text-green-600">{expert.performance.completedTasks}</div>
            <div className="text-xs text-gray-500">完成任务</div>
          </div>
          <div className="text-center p-3 bg-gray-50 rounded-lg">
            <div className="text-lg font-bold text-purple-600">{expert.performance.totalTasks}</div>
            <div className="text-xs text-gray-500">总任务数</div>
          </div>
          <div className="text-center p-3 bg-gray-50 rounded-lg">
            <div className="text-lg font-bold text-orange-600">
              {formatTime(expert.performance.averageCompletionTime)}
            </div>
            <div className="text-xs text-gray-500">平均完成时间</div>
          </div>
        </div>

        {/* Capabilities */}
        <div className="mb-4">
          <h4 className="text-sm font-medium text-gray-900 mb-2">能力标签</h4>
          <div className="flex flex-wrap gap-1">
            {expert.capabilities.map((capability, index) => (
              <Badge key={index} variant="info" size="sm">
                {capability}
              </Badge>
            ))}
          </div>
        </div>

        {/* Last Active */}
        <div className="text-xs text-gray-500 mb-4">
          最后活跃: {new Date(expert.performance.lastActive).toLocaleString()}
        </div>

        {/* Actions */}
        <div className="flex space-x-2 pt-4 border-t border-gray-200">
          {onView && (
            <button
              onClick={() => onView(expert.id)}
              className="text-blue-600 hover:text-blue-500 text-sm font-medium"
            >
              查看详情
            </button>
          )}
          {onConfigure && (
            <button
              onClick={() => onConfigure(expert.id)}
              className="text-gray-600 hover:text-gray-500 text-sm font-medium"
            >
              配置
            </button>
          )}
        </div>
      </CardContent>
    </Card>
  );
};

export { ExpertCard }; 