'use client';

import React from 'react';
import { Card } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { Team } from '@/hooks/useTeams';

interface TeamCardProps {
  team: Team;
}

const TeamCard: React.FC<TeamCardProps> = ({ team }) => {
  return (
    <Card className="p-4 flex justify-between items-center">
      <div>
        <h3 className="font-bold">{team.name}</h3>
        <p className="text-sm text-gray-400">
          {team.is_personal ? 'Personal' : 'Team'}
        </p>
      </div>
      <Badge>{team.role}</Badge>
    </Card>
  );
};

export default TeamCard; 