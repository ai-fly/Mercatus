'use client';

import React, { useState } from 'react';
import { useTeams } from '@/hooks/useTeams';
import TeamCard from '@/components/team/TeamCard';
import { Button } from '@/components/ui/Button';
import { Loading } from '@/components/ui/Loading';
import { EmptyState } from '@/components/ui/EmptyState';
import { Modal } from '@/components/ui/Modal';
import { Input } from '@/components/ui/Input';
import { useTranslations } from 'next-intl';
import { useSession } from 'next-auth/react';
import { Alert } from '@/components/ui/Alert';

const DashboardPage: React.FC = () => {
  const { teams, isLoading, error, mutate } = useTeams();
  const { data: session } = useSession();
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [newTeamName, setNewTeamName] = useState('');
  const [newTeamDescription, setNewTeamDescription] = useState('');
  const [isCreating, setIsCreating] = useState(false);
  const t = useTranslations('dashboard');

  const handleCreateTeam = async () => {
    if (!newTeamName) return;
    setIsCreating(true);
    try {
      // Use the new backendToken from the session
      const backendToken = session?.backendToken;
      if (!backendToken) {
        throw new Error('User is not authenticated');
      }

      const response = await fetch('/api/v1/teams', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          // Send the backendToken to your API
          Authorization: `Bearer ${backendToken}`,
        },
        body: JSON.stringify({ team_name: newTeamName, description: newTeamDescription }),
      });
      if (!response.ok) {
        throw new Error('Failed to create team');
      }
      await mutate(); // Re-fetch teams
      setIsModalOpen(false);
      setNewTeamName('');
      setNewTeamDescription('');
    } catch (error) {
      console.error(error);
      // You might want to show an error to the user
    } finally {
      setIsCreating(false);
    }
  };

  if (isLoading) {
    return <Loading />;
  }

  if (error) {
    return (
      <div className="flex h-full items-center justify-center p-8">
        <Alert type="error" title="Error loading teams">
          {error.info?.message || error.message}
        </Alert>
      </div>
    );
  }

  return (
    <div className="p-8">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-3xl font-bold">Your Teams</h1>
        <Button onClick={() => setIsModalOpen(true)}>Create New Team</Button>
      </div>
      {teams && teams.length > 0 ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {teams.map((team) => (
            <TeamCard key={team.id} team={team} />
          ))}
        </div>
      ) : (
        <EmptyState
          title="No Teams Found"
          description="You are not a part of any teams yet. Create one to get started."
        />
      )}

      <Modal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        title={t('createTeam')}
      >
        <div className="space-y-4">
          <div>
            <label htmlFor="teamName" className="block text-sm font-medium text-gray-700">
              {t('teamName')}
            </label>
            <Input
              id="teamName"
              value={newTeamName}
              onChange={(e) => setNewTeamName(e.target.value)}
              placeholder={t('teamNameRequired')}
            />
          </div>
          <div>
            <label htmlFor="teamDescription" className="block text-sm font-medium text-gray-700">
              {t('teamDescription')}
            </label>
            <Input
              id="teamDescription"
              value={newTeamDescription}
              onChange={(e) => setNewTeamDescription(e.target.value)}
              placeholder={t('teamDescriptionRequired')}
            />
          </div>
          <div className="flex justify-end space-x-2">
            <Button variant="outline" onClick={() => setIsModalOpen(false)}>
              Cancel
            </Button>
            <Button onClick={handleCreateTeam} disabled={isCreating}>
              {isCreating ? 'Creating...' : 'Create'}
            </Button>
          </div>
        </div>
      </Modal>
    </div>
  );
};

export default DashboardPage; 