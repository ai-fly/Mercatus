'use client';

import React from 'react';
import { Card } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { Bot, Cpu, Zap, Flag } from 'lucide-react';

const experts = [
  {
    name: 'Content Strategist',
    status: 'Active',
    task: 'Generating blog posts',
    performance: '98%',
    icon: Bot,
  },
  {
    name: 'SEO Optimizer',
    status: 'Idle',
    task: 'None',
    performance: '95%',
    icon: Cpu,
  },
  {
    name: 'Social Media Manager',
    status: 'Active',
    task: 'Scheduling tweets',
    performance: '99%',
    icon: Zap,
  },
  {
    name: 'Campaign Analyst',
    status: 'Error',
    task: 'Analyzing ad spend',
    performance: '75%',
    icon: Flag,
  },
];

const ExpertsPage: React.FC = () => {
  return (
    <div>
      <h1 className="text-3xl font-bold mb-6">Expert Instances</h1>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {experts.map((expert, index) => (
          <Card key={index} className="bg-gray-800 p-6 rounded-lg">
            <div className="flex items-center mb-4">
              <expert.icon className="h-8 w-8 text-blue-400 mr-4" />
              <h2 className="text-xl font-semibold">{expert.name}</h2>
            </div>
            <div className="space-y-2">
              <p>
                Status: <Badge variant={expert.status === 'Active' ? 'default' : expert.status === 'Error' ? 'destructive' : 'secondary'}>{expert.status}</Badge>
              </p>
              <p>Current Task: {expert.task}</p>
              <p>Performance: {expert.performance}</p>
            </div>
          </Card>
        ))}
      </div>
    </div>
  );
};

export default ExpertsPage; 