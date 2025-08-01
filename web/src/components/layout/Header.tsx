'use client';

import React, { useState } from 'react';
import { Button } from '@/components/ui/Button';
import { LanguageSwitcher } from '../ui/LanguageSwitcher';
import { ChevronDown, Bell, LogOut } from 'lucide-react';
import { useSession, signOut } from 'next-auth/react';
import { Link } from '@/i18n/navigation';
import Image from 'next/image';

const Header: React.FC = () => {
  const { data: session } = useSession();
  const [isDropdownOpen, setIsDropdownOpen] = useState(false);

  return (
    <header className="flex items-center justify-between p-4 bg-gray-900 border-b border-gray-700">
      <div>{/* Potentially a search bar or breadcrumbs can go here */}</div>
      <div className="flex items-center space-x-4">
        <Button variant="ghost" className="p-2">
          <Bell className="h-5 w-5" />
        </Button>
        <LanguageSwitcher />
        <div className="relative">
          {session ? (
            <>
              <div
                className="flex items-center space-x-2 cursor-pointer"
                onClick={() => setIsDropdownOpen(!isDropdownOpen)}
              >
                <Image
                  src={session.user?.image || 'https://i.pravatar.cc/40'}
                  alt={session.user?.name || 'User Avatar'}
                  width={32}
                  height={32}
                  className="rounded-full"
                />
                <span>{session.user?.email || 'User'}</span>
                <ChevronDown className={`h-4 w-4 transition-transform ${isDropdownOpen ? 'rotate-180' : ''}`} />
              </div>
              {isDropdownOpen && (
                <div className="absolute right-0 mt-2 w-48 bg-gray-800 rounded-md shadow-lg py-1 z-50">
                  <Button
                    variant="ghost"
                    className="w-full flex items-center justify-start px-4 py-2 text-sm text-gray-300 hover:bg-gray-700"
                    onClick={() => signOut({ callbackUrl: '/login' })}
                  >
                    <LogOut className="mr-2 h-4 w-4" />
                    Sign out
                  </Button>
                </div>
              )}
            </>
          ) : (
            <Link href="/login">
              <Button variant="secondary">Sign in</Button>
            </Link>
          )}
        </div>
      </div>
    </header>
  );
};

export default Header; 