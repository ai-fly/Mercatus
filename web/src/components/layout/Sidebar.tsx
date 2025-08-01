'use client';

import React from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { Globe, BarChart, Settings, Users, ClipboardList, Bot } from 'lucide-react';
import { Route } from 'next';
import Image from 'next/image';

const navLinks = [
  { href: '/dashboard', icon: BarChart, label: 'Dashboard' },
  { href: '/tasks', icon: ClipboardList, label: 'Tasks' },
  { href: '/experts', icon: Bot, label: 'Experts' },
  { href: '/team', icon: Users, label: 'Team' },
  { href: '/performance', icon: Globe, label: 'Performance' },
  { href: '/settings', icon: Settings, label: 'Settings' },
];

const Sidebar: React.FC = () => {
  const pathname = usePathname();

  return (
    <aside className="w-64 bg-gray-900 text-white flex flex-col p-4 border-r border-gray-700">
      <div className="flex items-center mb-8 space-x-2">
        <Image src="/file.svg" alt="Mercatus Logo" width={32} height={32} />
        <span className="text-xl font-bold">Mercatus</span>
      </div>
      <nav className="flex-1 space-y-2">
        {navLinks.map((link) => (
          <Link
            key={link.href}
            href={link.href as Route}
            className={`flex items-center p-3 rounded-lg transition-colors ${
              pathname === link.href
                ? 'bg-blue-500 text-white'
                : 'text-gray-400 hover:bg-gray-800 hover:text-white'
            }`}
          >
            <link.icon className="h-5 w-5 mr-3" />
            <span>{link.label}</span>
          </Link>
        ))}
      </nav>
    </aside>
  );
};

export default Sidebar; 