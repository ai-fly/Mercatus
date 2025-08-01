'use client';

import useSWR from 'swr';
import { useSession } from 'next-auth/react';

export interface Team {
  id: string;
  name: string;
  is_personal: boolean;
  role: 'owner' | 'member';
  created_at: string;
  updated_at: string;
}

export interface ApiError extends Error {
  info?: { message: string };
  status?: number;
}

const fetcher = (url: string, token: string) =>
  fetch(url, {
    headers: {
      Authorization: `Bearer ${token}`,
    },
  }).then(async (res) => {
    if (res.status === 404) {
      return []; // Treat 404 as an empty list of teams
    }
    if (!res.ok) {
      const error: ApiError = new Error('An error occurred while fetching the data.');
      // Attach extra info to the error object.
      try {
        error.info = await res.json();
      } catch {
        // The response might not be JSON.
        error.info = { message: await res.text() };
      }
      error.status = res.status;
      throw error;
    }
    return res.json();
  });

export const useTeams = () => {
  const { data: session, status } = useSession();
  const userId = session?.user?.id;
  const backendToken = session?.backendToken;

  const { data, error, isLoading, mutate } = useSWR<Team[], ApiError>(
    userId && backendToken ? [`/api/v1/users/${userId}/teams`, backendToken] : null,
    ([url, token]: [string, string]) => fetcher(url, token),
  );

  return {
    teams: data,
    isLoading: isLoading || status === 'loading',
    error,
    mutate,
  };
}; 