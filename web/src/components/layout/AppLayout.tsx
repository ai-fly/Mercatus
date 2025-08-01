'use client';

import React from 'react';
import Header from './Header';
import Sidebar from './Sidebar';
import { usePathname } from '@/i18n/navigation';

interface AppLayoutProps {
  children: React.ReactNode;
}

const AppLayout: React.FC<AppLayoutProps> = ({ children }) => {
  const pathname = usePathname();
  const isLoginPage = pathname === '/login';
  const isHomePage = pathname === '/';

  if (isLoginPage || isHomePage) {
    return <>{children}</>;
  }

  return (
    <div className="flex h-screen bg-gray-900 text-white">
      <Sidebar />
      <div className="flex-1 flex flex-col overflow-hidden">
        <Header />
        <main className="flex-1 overflow-x-hidden overflow-y-auto bg-gray-900 p-6">
          {children}
        </main>
      </div>
    </div>
  );
};

export default AppLayout; 