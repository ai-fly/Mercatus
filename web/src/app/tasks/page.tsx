'use client';

import React from 'react';
import { Card } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { Button } from '@/components/ui/Button';
import { PlusCircle, Filter } from 'lucide-react';

const tasks = [
  {
    title: 'Launch new ad campaign',
    status: 'In Progress',
    priority: 'High',
    dueDate: '2024-08-15',
  },
  {
    title: 'Write blog post on "AI in Marketing"',
    status: 'Todo',
    priority: 'Medium',
    dueDate: '2024-08-20',
  },
  {
    title: 'Analyze Q2 social media performance',
    status: 'Completed',
    priority: 'Low',
    dueDate: '2024-07-30',
  },
];

const TasksPage: React.FC = () => {
  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-3xl font-bold">Tasks</h1>
        <div className="flex items-center space-x-2">
          <Button variant="outline">
            <Filter className="h-4 w-4 mr-2" />
            Filter
          </Button>
          <Button>
            <PlusCircle className="h-4 w-4 mr-2" />
            New Task
          </Button>
        </div>
      </div>
      <div className="space-y-4">
        {tasks.map((task, index) => (
          <Card key={index} className="bg-gray-800 p-4 rounded-lg flex items-center justify-between">
            <div>
              <h2 className="text-lg font-semibold">{task.title}</h2>
              <p className="text-sm text-gray-400">Due: {task.dueDate}</p>
            </div>
            <div className="flex items-center space-x-4">
              <Badge
                variant={
                  task.priority === 'High'
                    ? 'destructive'
                    : task.priority === 'Medium'
                    ? 'secondary'
                    : 'default'
                }
              >
                {task.priority}
              </Badge>
              <Badge
                variant={
                  task.status === 'In Progress'
                    ? 'default'
                    : task.status === 'Completed'
                    ? 'secondary'
                    : 'outline'
                }
              >
                {task.status}
              </Badge>
              <Button variant="ghost" size="sm">
                View
              </Button>
            </div>
          </Card>
        ))}
      </div>
    </div>
  );
};

export default TasksPage; 