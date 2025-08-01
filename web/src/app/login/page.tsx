'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useTranslations } from 'next-intl';
import { Link } from '@/i18n/navigation';
import Image from 'next/image';
import { LoginBanner } from '@/components/login/LoginBanner';
import { useSession, signIn } from 'next-auth/react';

// No longer need global `window.google`, use types instead
// declare global {
//   interface Window {
//     google?: any;
//   }
// }

interface LoginFormData {
  email: string;
  password: string;
}

interface LoginResponse {
  token: string;
  user: {
    id: string;
    email: string;
    name: string;
  };
}

export default function LoginPage() {
  const router = useRouter();
  const t = useTranslations('auth');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [formData, setFormData] = useState<LoginFormData>({
    email: '',
    password: ''
  });
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
    signIn('google', { callbackUrl: '/dashboard' });
  };

  // Traditional email/password login (fallback)
  const handleEmailLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setError(null);

    try {
      const result = await fetch('/api/v1/auth/login', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(formData)
      });

      if (!result.ok) {
        throw new Error(t('loginError'));
      }

      const data: LoginResponse = await result.json();
      
      // Store token
      localStorage.setItem('auth_token', data.token);
      localStorage.setItem('user_info', JSON.stringify(data.user));
      
      // Redirect to dashboard
      router.push('/dashboard');
    } catch (err) {
      setError(err instanceof Error ? err.message : '登录失败，请重试');
      setIsLoading(false);
    }
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value
    });
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
      
      <main className="relative z-10 flex min-h-screen items-center justify-center p-4">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-16 items-center max-w-6xl w-full">
          {/* Left Side: Branding */}
          <div className="hidden lg:flex flex-col items-start space-y-6">
            <div className="flex items-center space-x-2">
              <Image src="/file.svg" alt="Mercatus Logo" width={32} height={32} />
              <span className="text-xl font-bold">Mercatus</span>
            </div>
            <h1 className="text-5xl font-extrabold leading-tight tracking-tighter">
              Dream, Chat, Create <br />
              Your 24/7 AI Team
            </h1>
            <LoginBanner />
          </div>

          {/* Right Side: Login Form */}
          <div className="w-full max-w-md bg-[#161429]/50 backdrop-blur-lg border border-slate-700/50 rounded-2xl p-8 shadow-2xl">
            <h2 className="text-3xl font-bold mb-8 text-center">Welcome Back</h2>
            
            {error && (
              <div className="bg-red-900/50 border border-red-500 text-red-300 px-4 py-3 rounded-lg relative mb-4" role="alert">
                <span className="block sm:inline">{error}</span>
              </div>
            )}

            {/* Google Login Button */}
            <button
              onClick={handleGoogleLogin}
              disabled={isLoading}
              className="w-full flex items-center justify-center gap-3 py-3 px-4 mb-4 bg-slate-800/50 border border-slate-700 rounded-lg text-white hover:bg-slate-700/70 transition-colors duration-300 disabled:opacity-50 cursor-pointer"
            >
              <svg className="w-5 h-5" viewBox="0 0 24 24" fill="currentColor">
                <path d="M22.56,12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26,1.37-1.04,2.53-2.21,3.31v2.77h3.57c2.08-1.92,3.28-4.74,3.28-8.09Z" />
                <path d="M12,23c2.97,0,5.46-.98,7.28-2.66l-3.57-2.77c-.98,.66-2.23,1.06-3.71,1.06-2.86,0-5.29-1.93-6.16-4.53H2.18v2.84C3.99,20.53,7.7,23,12,23Z" />
                <path d="M5.84,14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43,.35-2.09V7.07H2.18C1.43,8.55,1,10.22,1,12s.43,3.45,1.18,4.93l2.85-2.22.81-.62Z" />
                <path d="M12,5.38c1.62,0,3.06,.56,4.21,1.64l3.15-3.15C17.45,2.09,14.97,1,12,1,7.7,1,3.99,3.47,2.18,7.07l3.66,2.84c.87-2.6,3.3-4.53,6.16-4.53Z" />
              </svg>
              Sign in with Google
            </button>
            
            <div className="flex items-center my-6">
              <hr className="flex-grow border-slate-700" />
              <span className="mx-4 text-slate-400 text-sm">Or Sign in with a registered account</span>
              <hr className="flex-grow border-slate-700" />
            </div>

            <form onSubmit={handleEmailLogin} className="space-y-4">
              <div>
                <label htmlFor="email" className="sr-only">Email</label>
                <input
                  id="email"
                  name="email"
                  type="email"
                  autoComplete="email"
                  required
                  value={formData.email}
                  onChange={handleInputChange}
                  className="w-full bg-[#0c0a18] border border-slate-700 rounded-lg px-4 py-3 placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent transition-all"
                  placeholder="email"
                />
              </div>

              <div>
                <label htmlFor="password" className="sr-only">Password</label>
                <input
                  id="password"
                  name="password"
                  type="password"
                  autoComplete="current-password"
                  required
                  value={formData.password}
                  onChange={handleInputChange}
                  className="w-full bg-[#0c0a18] border border-slate-700 rounded-lg px-4 py-3 placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent transition-all"
                  placeholder="password"
                />
              </div>
              
              <div className="text-right text-sm text-slate-400">
                <Link href="#" className="hover:text-indigo-.300">
                  Reset your password
                </Link>
              </div>

              <div className="pt-2">
                <button
                  type="submit"
                  disabled={isLoading}
                  className="w-full bg-indigo-600 hover:bg-indigo-700 text-white font-bold py-3 rounded-lg transition-colors duration-300 disabled:opacity-50"
                >
                  {isLoading ? 'Signing in...' : 'Sign in'}
                </button>
              </div>
            </form>
            
            <div className="text-center text-sm text-slate-400 mt-6">
              Don&apos;t have an account?{' '}
              <Link href="#" className="font-medium text-indigo-400 hover:text-indigo-300">
                Sign up for an account
              </Link>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
} 