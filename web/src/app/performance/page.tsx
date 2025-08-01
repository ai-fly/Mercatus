'use client';

import React from 'react';
import { Card } from '@/components/ui/Card';
import { AreaChart, BarChart, LineChart, TrendingUp } from 'lucide-react';

const PerformancePage: React.FC = () => {
  return (
    <div>
      <h1 className="text-3xl font-bold mb-6">Team Performance</h1>
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card className="bg-gray-800 p-6 rounded-lg">
          <h2 className="text-xl font-semibold mb-4 flex items-center">
            <TrendingUp className="h-6 w-6 mr-2 text-green-400" />
            Overall Performance
          </h2>
          <div className="h-64 bg-gray-700 rounded-lg flex items-center justify-center">
            <p className="text-gray-400">Chart will be rendered here</p>
          </div>
        </Card>
        <Card className="bg-gray-800 p-6 rounded-lg">
          <h2 className="text-xl font-semibold mb-4 flex items-center">
            <BarChart className="h-6 w-6 mr-2 text-blue-400" />
            Task Completion Rate
          </h2>
          <div className="h-64 bg-gray-700 rounded-lg flex items-center justify-center">
            <p className="text-gray-400">Chart will be rendered here</p>
          </div>
        </Card>
        <Card className="bg-gray-800 p-6 rounded-lg">
          <h2 className="text-xl font-semibold mb-4 flex items-center">
            <AreaChart className="h-6 w-6 mr-2 text-purple-400" />
            Expert Activity
          </h2>
          <div className="h-64 bg-gray-700 rounded-lg flex items-center justify-center">
            <p className="text-gray-400">Chart will be rendered here</p>
          </div>
        </Card>
        <Card className="bg-gray-800 p-6 rounded-lg">
          <h2 className="text-xl font-semibold mb-4 flex items-center">
            <LineChart className="h-6 w-6 mr-2 text-yellow-400" />
            Campaign ROI
          </h2>
          <div className="h-64 bg-gray-700 rounded-lg flex items-center justify-center">
            <p className="text-gray-400">Chart will be rendered here</p>
          </div>
        </Card>
      </div>
    </div>
  );
};

export default PerformancePage; 