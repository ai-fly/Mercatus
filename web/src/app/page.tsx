'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { useTranslations } from 'next-intl';
import { Link } from '@/i18n/navigation';
import Image from 'next/image';
import { Button } from '@/components/ui';
import { useSession, signOut } from 'next-auth/react';

export default function RootPage() {
  const router = useRouter();
  const t = useTranslations('home');
  const [isLoading, setIsLoading] = useState(false);
  const { data: session } = useSession();

  const handleGetStarted = () => {
    setIsLoading(true);
    router.push('/dashboard');
  };

  return (
    <div className="relative min-h-screen w-full bg-[#111118] text-white overflow-hidden">
      {/* Background Gradient & Grid */}
      <div className="absolute inset-0 z-0">
        <div className="absolute inset-0 bg-gradient-to-br from-[#1e1a3b] via-[#111118] to-[#111118]"></div>
        <div 
          className="absolute inset-0 bg-[radial-gradient(circle_at_center,_rgba(255,255,255,0.04)_1px,_transparent_1px)] [background-size:2rem_2rem]"
        ></div>
      </div>

      <main className="relative z-10 flex flex-col min-h-screen">
        {/* Header */}
        <header className="w-full">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="flex justify-between items-center py-6">
              <div className="flex items-center space-x-2">
                <Image src="/file.svg" alt="Mercatus Logo" width={32} height={32} />
                <span className="text-xl font-bold">Mercatus</span>
              </div>
              <div className="flex items-center space-x-4">
                {session ? (
                  <Button
                    variant="outline"
                    className="border-slate-700 bg-transparent text-white hover:bg-slate-800"
                    onClick={() => signOut({ callbackUrl: '/' })}
                  >
                    {t('logout')}
                  </Button>
                ) : (
                  <Link href="/login">
                    <Button variant="outline" className="border-slate-700 bg-transparent text-white hover:bg-slate-800">
                      {t('login')}
                    </Button>
                  </Link>
                )}
                <Button
                  onClick={handleGetStarted}
                  disabled={isLoading}
                  className="bg-indigo-600 hover:bg-indigo-700"
                >
                  {isLoading ? t('loading') : t('getStarted')}
                </Button>
              </div>
            </div>
          </div>
        </header>
        
        {/* Hero Section */}
        <section className="flex-grow flex items-center justify-center text-center px-4">
          <div className="max-w-4xl">
            <h1 className="text-5xl md:text-7xl font-extrabold leading-tight tracking-tighter mb-6">
              {t('heroTitle')}
            </h1>
            <p className="text-lg md:text-xl text-slate-400 max-w-2xl mx-auto mb-10">
             {t('heroSubtitle')}
            </p>
            <Button
              size="lg"
              onClick={handleGetStarted}
              disabled={isLoading}
              className="bg-indigo-600 hover:bg-indigo-700 text-lg px-8 py-6"
            >
              {isLoading ? t('loading') : t('cta')}
            </Button>
          </div>
        </section>

        {/* Footer */}
        <footer className="w-full py-6">
          <div className="text-center text-slate-500 text-sm">
            © {new Date().getFullYear()} Mercatus. All rights reserved.
          </div>
        </footer>
      </main>
    </div>
  );
}
