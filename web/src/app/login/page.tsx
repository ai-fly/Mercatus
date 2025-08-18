'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useTranslations } from 'next-intl';
import { Link } from '@/i18n/navigation';
import Image from 'next/image';
import { LoginBanner } from '@/components/login/LoginBanner';
import { useSession, signIn } from 'next-auth/react';

export default function LoginPage() {
  const router = useRouter();
  const t = useTranslations('auth');
  const [isLoading, setIsLoading] = useState(false);
  const { data: session } = useSession();

  useEffect(() => {
    if (session) {
      router.push('/dashboard');
    }
  }, [session, router]);

  if (session) {
    return null;
  }

  // Google OAuth login
  const handleGoogleLogin = async () => {
    setIsLoading(true);
    try {
      await signIn('google', { callbackUrl: '/dashboard' });
    } catch (error) {
      console.error('Google login error:', error);
      setIsLoading(false);
    }
  };

  return (
    <div className="relative min-h-screen w-full bg-[#0a0a0f] text-white overflow-hidden">
      {/* Background Effects */}
      <div className="fixed inset-0 z-0">
        <div className="absolute inset-0 bg-gradient-to-br from-[#1a1a2e] via-[#0a0a0f] to-[#0f0f23]"></div>
        <div className="absolute inset-0 bg-[radial-gradient(circle_at_center,_rgba(99,102,241,0.1)_0%,_transparent_50%)]"></div>
        <div 
          className="absolute inset-0 bg-[radial-gradient(circle_at_center,_rgba(255,255,255,0.02)_1px,_transparent_1px)] [background-size:3rem_3rem]"
        ></div>
      </div>
      
      <main className="relative z-10 flex min-h-screen items-center justify-center p-4">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-16 items-center max-w-6xl w-full">
          {/* Left Side: Branding */}
          <div className="hidden lg:flex flex-col items-start space-y-8">
            <Link href="/" className="flex items-center space-x-3">
              <div className="w-10 h-10 bg-gradient-to-r from-indigo-500 to-purple-600 rounded-xl flex items-center justify-center">
                <span className="text-xl font-bold">M</span>
              </div>
              <span className="text-2xl font-bold bg-gradient-to-r from-white to-gray-300 bg-clip-text text-transparent">
                Mercatus
              </span>
            </Link>
            
            <div className="space-y-6">
              <h1 className="text-5xl font-extrabold leading-tight tracking-tighter">
                <span className="bg-gradient-to-r from-white via-gray-100 to-gray-300 bg-clip-text text-transparent">
                  Welcome to the Future <br />
                  of AI Marketing
                </span>
              </h1>
              <p className="text-xl text-gray-400 leading-relaxed max-w-md">
                Join thousands of companies using AI to transform their marketing operations.
              </p>
            </div>
            
            <LoginBanner />
          </div>

          {/* Right Side: Login Form */}
          <div className="w-full max-w-md mx-auto">
            <div className="bg-gradient-to-br from-slate-900/50 to-slate-800/30 backdrop-blur-sm border border-slate-700/50 rounded-2xl p-8 shadow-xl">
              <div className="text-center mb-8">
                <div className="lg:hidden mb-6">
                  <Link href="/" className="flex items-center justify-center space-x-3">
                    <div className="w-10 h-10 bg-gradient-to-r from-indigo-500 to-purple-600 rounded-xl flex items-center justify-center">
                      <span className="text-xl font-bold">M</span>
                    </div>
                    <span className="text-2xl font-bold bg-gradient-to-r from-white to-gray-300 bg-clip-text text-transparent">
                      Mercatus
                    </span>
                  </Link>
                </div>
                
                <h2 className="text-3xl font-bold mb-2 bg-gradient-to-r from-white to-gray-300 bg-clip-text text-transparent">
                  {t('welcome')}
                </h2>
                <p className="text-gray-400">
                  Sign in to access your AI marketing team
                </p>
              </div>

              {/* Google Login Button */}
              <button
                onClick={handleGoogleLogin}
                disabled={isLoading}
                className="w-full flex items-center justify-center gap-3 py-4 px-6 bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-700 hover:to-purple-700 border border-indigo-500/50 rounded-xl text-white font-semibold transition-all duration-300 disabled:opacity-50 disabled:cursor-not-allowed transform hover:scale-105 shadow-lg shadow-indigo-500/25"
              >
                {isLoading ? (
                  <>
                    <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                    </svg>
                    Signing in...
                  </>
                ) : (
                  <>
                    <svg className="w-5 h-5" viewBox="0 0 24 24" fill="currentColor">
                      <path d="M22.56,12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26,1.37-1.04,2.53-2.21,3.31v2.77h3.57c2.08-1.92,3.28-4.74,3.28-8.09Z" />
                      <path d="M12,23c2.97,0,5.46-.98,7.28-2.66l-3.57-2.77c-.98,.66-2.23,1.06-3.71,1.06-2.86,0-5.29-1.93-6.16-4.53H2.18v2.84C3.99,20.53,7.7,23,12,23Z" />
                      <path d="M5.84,14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43,.35-2.09V7.07H2.18C1.43,8.55,1,10.22,1,12s.43,3.45,1.18,4.93l2.85-2.22.81-.62Z" />
                      <path d="M12,5.38c1.62,0,3.06,.56,4.21,1.64l3.15-3.15C17.45,2.09,14.97,1,12,1,7.7,1,3.99,3.47,2.18,7.07l3.66,2.84c.87-2.6,3.3-4.53,6.16-4.53Z" />
                    </svg>
                    {t('googleLogin')}
                  </>
                )}
              </button>
              
              <div className="mt-8 text-center">
                <div className="text-sm text-gray-400 mb-4">
                  By signing in, you agree to our Terms of Service and Privacy Policy
                </div>
                
                <Link 
                  href="/" 
                  className="text-indigo-400 hover:text-indigo-300 text-sm font-medium transition-colors duration-300"
                >
                  ← Back to Home
                </Link>
              </div>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}