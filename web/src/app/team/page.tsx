'use client';

import React from 'react';
import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { PlusCircle, UserPlus } from 'lucide-react';

const teamMembers = [
  {
    name: 'Alice Johnson',
    role: 'Project Manager',
    avatar: 'https://i.pravatar.cc/150?u=a042581f4e29026704d',
  },
  {
    name: 'Bob Williams',
    role: 'Lead Developer',
    avatar: 'https://i.pravatar.cc/150?u=a042581f4e29026704e',
  },
  {
    name: 'Charlie Brown',
    role: 'UI/UX Designer',
    avatar: 'https://i.pravatar.cc/150?u=a042581f4e29026704f',
  },
];

const TeamPage: React.FC = () => {
  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-3xl font-bold">Our Team</h1>
        <Button>
          <UserPlus className="h-4 w-4 mr-2" />
          Invite Member
        </Button>
      </div>
      <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-6">
        {teamMembers.map((member, index) => (
          <Card key={index} className="bg-gray-800 p-6 rounded-lg text-center">
            <img
              src={member.avatar}
              alt={member.name}
              className="w-24 h-24 rounded-full mx-auto mb-4"
            />
            <h2 className="text-xl font-semibold">{member.name}</h2>
            <p className="text-gray-400">{member.role}</p>
          </Card>
        ))}
        <Card className="bg-gray-800 p-6 rounded-lg text-center flex flex-col items-center justify-center border-2 border-dashed border-gray-700 hover:border-blue-500 transition-colors">
           <PlusCircle className="h-12 w-12 text-gray-600 mb-4" />
           <h2 className="text-xl font-semibold">Add New Member</h2>
        </Card>
      </div>
    </div>
  );
};

export default TeamPage; 