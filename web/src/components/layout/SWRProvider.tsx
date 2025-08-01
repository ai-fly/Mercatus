'use client';

import { SWRConfig } from 'swr';
import { useRouter } from 'next/navigation';
import { signOut } from 'next-auth/react';

const SWRProvider = ({ children }: { children: React.ReactNode }) => {
  const router = useRouter();

  return (
    <SWRConfig
      value={{
        onError: (error) => {
          if (error.status === 401) {
            // Sign out the user and redirect to login
            signOut({ callbackUrl: '/login' });
          }
        },
      }}
    >
      {children}
    </SWRConfig>
  );
};

export default SWRProvider; 