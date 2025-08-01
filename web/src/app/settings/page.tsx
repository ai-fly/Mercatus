'use client';

import React from 'react';
import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { User, Bell, Lock, LogOut } from 'lucide-react';

const SettingsPage: React.FC = () => {
  return (
    <div>
      <h1 className="text-3xl font-bold mb-6">Settings</h1>
      <div className="space-y-8">
        <Card className="bg-gray-800 p-6 rounded-lg">
          <h2 className="text-xl font-semibold mb-4 flex items-center">
            <User className="h-6 w-6 mr-2 text-blue-400" />
            Profile
          </h2>
          <div className="space-y-4">
            <Input label="Name" defaultValue="John Doe" />
            <Input label="Email" defaultValue="john.doe@example.com" type="email" />
            <Button>Update Profile</Button>
          </div>
        </Card>

        <Card className="bg-gray-800 p-6 rounded-lg">
          <h2 className="text-xl font-semibold mb-4 flex items-center">
            <Lock className="h-6 w-6 mr-2 text-blue-400" />
            Password
          </h2>
          <div className="space-y-4">
            <Input label="Current Password" type="password" />
            <Input label="New Password" type="password" />
            <Input label="Confirm New Password" type="password" />
            <Button>Change Password</Button>
          </div>
        </Card>

        <Card className="bg-gray-800 p-6 rounded-lg">
          <h2 className="text-xl font-semibold mb-4 flex items-center">
            <Bell className="h-6 w-6 mr-2 text-blue-400" />
            Notifications
          </h2>
          {/* Add notification settings toggles here */}
        </Card>

        <Card className="bg-gray-800 p-6 rounded-lg">
          <h2 className="text-xl font-semibold mb-4 flex items-center">
            <LogOut className="h-6 w-6 mr-2 text-red-500" />
            Logout
          </h2>
          <p className="text-gray-400 mb-4">
            You will be logged out of your account on this device.
          </p>
          <Button variant="danger">Logout</Button>
        </Card>
      </div>
    </div>
  );
};

export default SettingsPage; 