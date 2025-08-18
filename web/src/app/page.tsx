'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useTranslations } from 'next-intl';
import { Link } from '@/i18n/navigation';
import Image from 'next/image';
import { Button } from '@/components/ui';
import { useSession, signOut } from 'next-auth/react';

// Enhanced Icons for new features
const CheckIcon = () => (
  <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
  </svg>
);

const ArrowRightIcon = () => (
  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
  </svg>
);

const PlayIcon = () => (
  <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14.828 14.828a4 4 0 01-5.656 0M9 10h1m4 0h1m-6 4h.01M19 10a9 9 0 11-18 0 9 9 0 0118 0z" />
  </svg>
);

// AI Agent Icons
const JeffIcon = () => (
  <svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
  </svg>
);

const MonicaIcon = () => (
  <svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
  </svg>
);

const HenryIcon = () => (
  <svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
  </svg>
);

// Feature Icons
const TrendingIcon = () => (
  <svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
  </svg>
);

const PublishIcon = () => (
  <svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
  </svg>
);

const TransparencyIcon = () => (
  <svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
  </svg>
);

const DataIcon = () => (
  <svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 8v8m-4-5v5m-4-2v2m-2 4h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
  </svg>
);

const GlobalIcon = () => (
  <svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3.055 11H5a2 2 0 012 2v1a2 2 0 002 2 2 2 0 012 2v2.945M8 3.935V5.5A2.5 2.5 0 0010.5 8h.5a2 2 0 012 2 2 2 0 104 0 2 2 0 012-2h1.064M15 20.488V18a2 2 0 012-2h3.064M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
  </svg>
);

const IntegrationIcon = () => (
  <svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 4a2 2 0 114 0v1a1 1 0 001 1h3a1 1 0 011 1v3a1 1 0 01-1 1h-1a2 2 0 100 4h1a1 1 0 011 1v3a1 1 0 01-1 1h-3a1 1 0 01-1-1v-1a2 2 0 10-4 0v1a1 1 0 01-1 1H7a1 1 0 01-1-1v-3a1 1 0 00-1-1H4a1 1 0 01-1-1V9a1 1 0 011-1h1a2 2 0 100-4H4a1 1 0 01-1-1V4a1 1 0 011-1h3a1 1 0 001-1z" />
  </svg>
);

// Platform Icons
const TwitterIcon = () => (
  <svg className="w-6 h-6" fill="currentColor" viewBox="0 0 24 24">
    <path d="M23.953 4.57a10 10 0 01-2.825.775 4.958 4.958 0 002.163-2.723c-.951.555-2.005.959-3.127 1.184a4.92 4.92 0 00-8.384 4.482C7.69 8.095 4.067 6.13 1.64 3.162a4.822 4.822 0 00-.666 2.475c0 1.71.87 3.213 2.188 4.096a4.904 4.904 0 01-2.228-.616v.06a4.923 4.923 0 003.946 4.827 4.996 4.996 0 01-2.212.085 4.936 4.936 0 004.604 3.417 9.867 9.867 0 01-6.102 2.105c-.39 0-.779-.023-1.17-.067a13.995 13.995 0 007.557 2.209c9.053 0 13.998-7.496 13.998-13.985 0-.21 0-.42-.015-.63A9.935 9.935 0 0024 4.59z"/>
  </svg>
);

const LinkedInIcon = () => (
  <svg className="w-6 h-6" fill="currentColor" viewBox="0 0 24 24">
    <path d="M20.447 20.452h-3.554v-5.569c0-1.328-.027-3.037-1.852-3.037-1.853 0-2.136 1.445-2.136 2.939v5.667H9.351V9h3.414v1.561h.046c.477-.9 1.637-1.85 3.37-1.85 3.601 0 4.267 2.37 4.267 5.455v6.286zM5.337 7.433c-1.144 0-2.063-.926-2.063-2.065 0-1.138.92-2.063 2.063-2.063 1.14 0 2.064.925 2.064 2.063 0 1.139-.925 2.065-2.064 2.065zm1.782 13.019H3.555V9h3.564v11.452zM22.225 0H1.771C.792 0 0 .774 0 1.729v20.542C0 23.227.792 24 1.771 24h20.451C23.2 24 24 23.227 24 22.271V1.729C24 .774 23.2 0 22.222 0h.003z"/>
  </svg>
);

const InstagramIcon = () => (
  <svg className="w-6 h-6" fill="currentColor" viewBox="0 0 24 24">
    <path d="M12 2.163c3.204 0 3.584.012 4.85.07 3.252.148 4.771 1.691 4.919 4.919.058 1.265.069 1.645.069 4.849 0 3.205-.012 3.584-.069 4.849-.149 3.225-1.664 4.771-4.919 4.919-1.266.058-1.644.07-4.85.07-3.204 0-3.584-.012-4.849-.07-3.26-.149-4.771-1.699-4.919-4.92-.058-1.265-.07-1.644-.07-4.849 0-3.204.013-3.583.07-4.849.149-3.227 1.664-4.771 4.919-4.919 1.266-.057 1.645-.069 4.849-.069zm0-2.163c-3.259 0-3.667.014-4.947.072-4.358.2-6.78 2.618-6.98 6.98-.059 1.281-.073 1.689-.073 4.948 0 3.259.014 3.668.072 4.948.2 4.358 2.618 6.78 6.98 6.98 1.281.058 1.689.072 4.948.072 3.259 0 3.668-.014 4.948-.072 4.354-.2 6.782-2.618 6.979-6.98.059-1.28.073-1.689.073-4.948 0-3.259-.014-3.667-.072-4.947-.196-4.354-2.617-6.78-6.979-6.98-1.281-.059-1.69-.073-4.949-.073zm0 5.838c-3.403 0-6.162 2.759-6.162 6.162s2.759 6.163 6.162 6.163 6.162-2.759 6.162-6.163c0-3.403-2.759-6.162-6.162-6.162zm0 10.162c-2.209 0-4-1.79-4-4 0-2.209 1.791-4 4-4s4 1.791 4 4c0 2.21-1.791 4-4 4zm6.406-11.845c-.796 0-1.441.645-1.441 1.44s.645 1.44 1.441 1.44c.795 0 1.439-.645 1.439-1.44s-.644-1.44-1.439-1.44z"/>
  </svg>
);

const TikTokIcon = () => (
  <svg className="w-6 h-6" fill="currentColor" viewBox="0 0 24 24">
    <path d="M12.525.02c1.31-.02 2.61-.01 3.91-.02.08 1.53.63 3.09 1.75 4.17 1.12 1.11 2.7 1.62 4.24 1.79v4.03c-1.44-.05-2.89-.35-4.2-.97-.57-.26-1.1-.59-1.62-.93-.01 2.92.01 5.84-.02 8.75-.08 1.4-.54 2.79-1.35 3.94-1.31 1.92-3.58 3.17-5.91 3.21-1.43.08-2.86-.31-4.08-1.03-2.02-1.19-3.44-3.37-3.65-5.71-.02-.5-.03-1-.01-1.49.18-1.9 1.12-3.72 2.58-4.96 1.66-1.44 3.98-2.13 6.15-1.72.02 1.48-.04 2.96-.04 4.44-.99-.32-2.15-.23-3.02.37-.63.41-1.11 1.04-1.36 1.75-.21.51-.15 1.07-.14 1.61.24 1.64 1.82 3.02 3.5 2.87 1.12-.01 2.19-.66 2.77-1.61.19-.33.4-.67.41-1.06.1-1.79.06-3.57.07-5.36.01-4.03-.01-8.05.02-12.07z"/>
  </svg>
);

// Animated Counter Component
const AnimatedCounter = ({ end, duration = 2000 }: { end: string; duration?: number }) => {
  const [count, setCount] = useState('0');
  const [hasStarted, setHasStarted] = useState(false);

  useEffect(() => {
    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting && !hasStarted) {
          setHasStarted(true);
          
          if (end.includes('x')) {
            const numEnd = parseInt(end.replace('x', ''));
            let current = 0;
            const increment = numEnd / (duration / 50);
            const timer = setInterval(() => {
              current += increment;
              if (current >= numEnd) {
                setCount(`${numEnd}x`);
                clearInterval(timer);
              } else {
                setCount(`${Math.floor(current)}x`);
              }
            }, 50);
          } else if (end.includes('%')) {
            const numEnd = parseInt(end.replace('%', ''));
            let current = 0;
            const increment = numEnd / (duration / 50);
            const timer = setInterval(() => {
              current += increment;
              if (current >= numEnd) {
                setCount(`${numEnd}%`);
                clearInterval(timer);
              } else {
                setCount(`${Math.floor(current)}%`);
              }
            }, 50);
          } else if (end === '24/7') {
            setCount('24/7');
          } else if (end.includes('+')) {
            const numEnd = parseInt(end.replace('+', ''));
            let current = 0;
            const increment = numEnd / (duration / 50);
            const timer = setInterval(() => {
              current += increment;
              if (current >= numEnd) {
                setCount(`${numEnd}+`);
                clearInterval(timer);
              } else {
                setCount(`${Math.floor(current)}+`);
              }
            }, 50);
          }
        }
      },
      { threshold: 0.5 }
    );

    const element = document.getElementById(`counter-${end}`);
    if (element) observer.observe(element);

    return () => observer.disconnect();
  }, [end, duration, hasStarted]);

  return <span id={`counter-${end}`}>{count}</span>;
};

export default function RootPage() {
  const router = useRouter();
  const t = useTranslations('home');
  const [isLoading, setIsLoading] = useState(false);
  const { data: session } = useSession();

  const handleGetStarted = () => {
    setIsLoading(true);
    router.push('/dashboard');
  };

  // AI Agents
  const agents = [
    {
      icon: <JeffIcon />,
      name: 'Jeff',
      role: 'Planning Expert',
      description: 'Strategic leader analyzing global trends and creating content strategies for international markets.',
      color: 'from-blue-500 to-cyan-500',
    },
    {
      icon: <MonicaIcon />,
      name: 'Monica',
      role: 'Execution Expert',
      description: 'Multi-language content creator generating diverse content formats across platforms.',
      color: 'from-purple-500 to-pink-500',
    },
    {
      icon: <HenryIcon />,
      name: 'Henry',
      role: 'Evaluation Expert',
      description: 'Quality controller ensuring cultural adaptation and compliance across all markets.',
      color: 'from-green-500 to-emerald-500',
    },
  ];

  // Core Features
  const coreFeatures = [
    {
      icon: <TrendingIcon />,
      title: 'Global Trending Search',
      description: 'Real-time monitoring of global hotspots across multiple languages and cultures.',
      features: ['Multi-language monitoring', 'Cultural sensitivity analysis', 'Cross-platform data integration'],
    },
    {
      icon: <PublishIcon />,
      title: 'Smart Publishing System',
      description: 'Automated and manual publishing modes with intelligent content routing.',
      features: ['Auto-publish with quality thresholds', 'Human review workflows', 'Multi-platform sync'],
    },
    {
      icon: <TransparencyIcon />,
      title: 'Full Transparency',
      description: 'Complete visibility into AI team operations with real-time monitoring.',
      features: ['Live workflow visualization', 'Decision process tracking', 'User intervention controls'],
    },
    {
      icon: <DataIcon />,
      title: 'Data-Driven Optimization',
      description: 'Collect third-party platform data to optimize marketing strategies.',
      features: ['Performance analytics', 'Strategy iteration', 'ROI calculation'],
    },
  ];

  // Platform Integrations
  const platforms = [
    { icon: <TwitterIcon />, name: 'Twitter', color: 'text-blue-400' },
    { icon: <LinkedInIcon />, name: 'LinkedIn', color: 'text-blue-600' },
    { icon: <InstagramIcon />, name: 'Instagram', color: 'text-pink-500' },
    { icon: <TikTokIcon />, name: 'TikTok', color: 'text-gray-800' },
  ];

  // Stats
  const stats = [
    { number: '5x', label: 'Content Production Speed' },
    { number: '70%', label: 'Cost Reduction' },
    { number: '7+', label: 'Languages Supported' },
    { number: '24/7', label: 'Global Monitoring' },
  ];

  // Process Steps
  const steps = [
    {
      number: '01',
      title: 'Trend Discovery',
      description: 'AI monitors global trends and hotspots across multiple platforms and languages.',
    },
    {
      number: '02',
      title: 'Strategy Planning',
      description: 'Jeff analyzes trends and creates culturally-adapted content strategies.',
    },
    {
      number: '03',
      title: 'Content Creation',
      description: 'Monica generates multi-language content optimized for different markets.',
    },
    {
      number: '04',
      title: 'Quality Control',
      description: 'Henry evaluates content quality, cultural fit, and compliance.',
    },
    {
      number: '05',
      title: 'Smart Publishing',
      description: 'Automated or manual publishing with real-time performance tracking.',
    },
    {
      number: '06',
      title: 'Data Analysis',
      description: 'Collect platform data to optimize future content strategies.',
    },
  ];

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

      <main className="relative z-10">
        {/* Header */}
        <header className="w-full backdrop-blur-sm bg-black/20 border-b border-white/10 sticky top-0 z-50">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="flex justify-between items-center py-4">
              <div className="flex items-center space-x-3">
                <div className="w-10 h-10 bg-gradient-to-r from-indigo-500 to-purple-600 rounded-xl flex items-center justify-center">
                  <span className="text-xl font-bold">M</span>
                </div>
                <span className="text-2xl font-bold bg-gradient-to-r from-white to-gray-300 bg-clip-text text-transparent">
                  Mercatus Content Factory
                </span>
              </div>
              <div className="flex items-center space-x-4">
                {session ? (
                  <Button
                    variant="outline"
                    className="border-slate-700 bg-transparent text-white hover:bg-slate-800 transition-all duration-300"
                    onClick={() => signOut({ callbackUrl: '/' })}
                  >
                    Logout
                  </Button>
                ) : (
                  <Link href="/login">
                    <Button variant="outline" className="border-slate-700 bg-transparent text-white hover:bg-slate-800 transition-all duration-300">
                      Login
                    </Button>
                  </Link>
                )}
                <Button
                  onClick={handleGetStarted}
                  disabled={isLoading}
                  className="bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-700 hover:to-purple-700 transition-all duration-300 transform hover:scale-105"
                >
                  {isLoading ? 'Loading...' : 'Get Started'}
                </Button>
              </div>
            </div>
          </div>
        </header>
        
        {/* Hero Section */}
        <section className="min-h-screen flex items-center justify-center px-4 pt-20">
          <div className="max-w-6xl mx-auto text-center">
            <div className="mb-8">
              <span className="inline-flex items-center px-4 py-2 rounded-full text-sm bg-gradient-to-r from-indigo-500/20 to-purple-500/20 border border-indigo-500/30 text-indigo-300 mb-8">
                🌍 Global AI Content Factory
              </span>
            </div>
            
            <h1 className="text-6xl md:text-8xl font-extrabold leading-tight tracking-tighter mb-8">
              <span className="bg-gradient-to-r from-white via-gray-100 to-gray-300 bg-clip-text text-transparent">
                AI Content Team
              </span>
              <br />
              <span className="bg-gradient-to-r from-indigo-400 via-purple-400 to-pink-400 bg-clip-text text-transparent">
                For Global Markets
              </span>
            </h1>
            
            <p className="text-lg md:text-xl text-gray-400 max-w-4xl mx-auto mb-12 leading-relaxed">
              Meet Jeff, Monica, and Henry - your AI content team that monitors global trends, creates multi-language content, 
              and publishes across platforms with complete transparency and data-driven optimization.
            </p>
            
            <div className="flex flex-col sm:flex-row gap-4 justify-center items-center mb-16">
              <Button
                size="lg"
                onClick={handleGetStarted}
                disabled={isLoading}
                className="bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-700 hover:to-purple-700 text-lg px-8 py-6 rounded-xl transition-all duration-300 transform hover:scale-105 shadow-lg shadow-indigo-500/25"
              >
                {isLoading ? 'Loading...' : 'Start Creating Content'}
                <ArrowRightIcon />
              </Button>
              
              <Button
                size="lg"
                variant="outline"
                className="border-slate-600 bg-transparent text-white hover:bg-slate-800 text-lg px-8 py-6 rounded-xl transition-all duration-300"
              >
                <PlayIcon />
                Watch Demo
              </Button>
            </div>

            {/* Platform Integration Preview */}
            <div className="flex justify-center items-center space-x-8 opacity-60">
              <span className="text-sm text-gray-500">Publish to:</span>
              {platforms.map((platform, index) => (
                <div key={index} className={`${platform.color} hover:scale-110 transition-transform`}>
                  {platform.icon}
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* Stats Section */}
        <section className="py-24 px-4 bg-gradient-to-r from-indigo-900/20 to-purple-900/20 backdrop-blur-sm">
          <div className="max-w-6xl mx-auto">
            <div className="grid grid-cols-2 md:grid-cols-4 gap-8">
              {stats.map((stat, index) => (
                <div key={index} className="text-center">
                  <div className="text-4xl md:text-6xl font-bold text-indigo-400 mb-2">
                    <AnimatedCounter end={stat.number} />
                  </div>
                  <div className="text-gray-400 text-sm md:text-base">{stat.label}</div>
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* AI Agents Section */}
        <section className="py-24 px-4">
          <div className="max-w-7xl mx-auto">
            <div className="text-center mb-16">
              <h2 className="text-4xl md:text-5xl font-bold mb-6 bg-gradient-to-r from-white to-gray-300 bg-clip-text text-transparent">
                Meet Your AI Content Team
              </h2>
              <p className="text-xl text-gray-400 max-w-3xl mx-auto">
                Three specialized AI agents working together through BlackBoard architecture for optimal content creation
              </p>
            </div>
            
            <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
              {agents.map((agent, index) => (
                <div
                  key={index}
                  className="p-8 rounded-2xl bg-gradient-to-br from-slate-900/50 to-slate-800/30 border border-slate-700/50 backdrop-blur-sm hover:border-indigo-500/50 transition-all duration-300 transform hover:scale-105"
                >
                  <div className={`w-16 h-16 bg-gradient-to-r ${agent.color} rounded-2xl flex items-center justify-center text-white mb-6 mx-auto`}>
                    {agent.icon}
                  </div>
                  <div className="text-center">
                    <h3 className="text-2xl font-bold mb-2 text-white">{agent.name}</h3>
                    <div className={`text-sm font-semibold mb-4 bg-gradient-to-r ${agent.color} bg-clip-text text-transparent`}>
                      {agent.role}
                    </div>
                    <p className="text-gray-400 leading-relaxed">{agent.description}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* Core Features Section */}
        <section className="py-24 px-4 bg-gradient-to-r from-slate-900/50 to-slate-800/30">
          <div className="max-w-7xl mx-auto">
            <div className="text-center mb-16">
              <h2 className="text-4xl md:text-5xl font-bold mb-6 bg-gradient-to-r from-white to-gray-300 bg-clip-text text-transparent">
                Powerful Features for Global Content
              </h2>
            </div>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-12">
              {coreFeatures.map((feature, index) => (
                <div
                  key={index}
                  className="p-8 rounded-2xl bg-gradient-to-br from-slate-900/50 to-slate-800/30 border border-slate-700/50 backdrop-blur-sm"
                >
                  <div className="text-indigo-400 mb-6">{feature.icon}</div>
                  <h3 className="text-2xl font-bold mb-4 text-white">{feature.title}</h3>
                  <p className="text-gray-400 mb-6 leading-relaxed">{feature.description}</p>
                  <ul className="space-y-2">
                    {feature.features.map((item, idx) => (
                      <li key={idx} className="flex items-center text-gray-300">
                        <CheckIcon />
                        <span className="ml-2">{item}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* Process Flow Section */}
        <section className="py-24 px-4">
          <div className="max-w-7xl mx-auto">
            <div className="text-center mb-16">
              <h2 className="text-4xl md:text-5xl font-bold mb-6 bg-gradient-to-r from-white to-gray-300 bg-clip-text text-transparent">
                How It Works
              </h2>
              <p className="text-xl text-gray-400 max-w-3xl mx-auto">
                From global trend discovery to data-driven optimization - a complete content lifecycle
              </p>
            </div>
            
            {/* Desktop: 2 rows of 3 columns */}
            <div className="hidden lg:block">
              {/* First Row */}
              <div className="grid grid-cols-3 gap-12 mb-16 relative">
                {/* Connection lines for first row */}
                <div className="absolute top-8 left-1/3 w-1/3 h-0.5 bg-gradient-to-r from-indigo-500 to-purple-500 transform -translate-x-1/2"></div>
                <div className="absolute top-8 left-2/3 w-1/3 h-0.5 bg-gradient-to-r from-purple-500 to-pink-500 transform -translate-x-1/2"></div>
                
                {steps.slice(0, 3).map((step, index) => (
                  <div key={index} className="text-center relative">
                    <div className="w-16 h-16 bg-gradient-to-r from-indigo-600 to-purple-600 rounded-2xl flex items-center justify-center text-2xl font-bold mx-auto mb-6 relative z-10 shadow-lg shadow-indigo-500/25">
                      {step.number}
                    </div>
                    <h3 className="text-xl font-bold mb-4 text-white">{step.title}</h3>
                    <p className="text-gray-400 leading-relaxed">{step.description}</p>
                  </div>
                ))}
              </div>
              
              {/* Vertical connection to second row */}
              <div className="flex justify-center mb-8">
                <div className="w-0.5 h-12 bg-gradient-to-b from-pink-500 to-indigo-500"></div>
              </div>
              
              {/* Second Row */}
              <div className="grid grid-cols-3 gap-12 relative">
                {/* Connection lines for second row */}
                <div className="absolute top-8 left-1/3 w-1/3 h-0.5 bg-gradient-to-r from-indigo-500 to-purple-500 transform -translate-x-1/2"></div>
                <div className="absolute top-8 left-2/3 w-1/3 h-0.5 bg-gradient-to-r from-purple-500 to-pink-500 transform -translate-x-1/2"></div>
                
                {steps.slice(3, 6).map((step, index) => (
                  <div key={index + 3} className="text-center relative">
                    <div className="w-16 h-16 bg-gradient-to-r from-purple-600 to-pink-600 rounded-2xl flex items-center justify-center text-2xl font-bold mx-auto mb-6 relative z-10 shadow-lg shadow-purple-500/25">
                      {step.number}
                    </div>
                    <h3 className="text-xl font-bold mb-4 text-white">{step.title}</h3>
                    <p className="text-gray-400 leading-relaxed">{step.description}</p>
                  </div>
                ))}
              </div>
            </div>
            
            {/* Mobile & Tablet: Single column with vertical flow */}
            <div className="lg:hidden space-y-12">
              {steps.map((step, index) => (
                <div key={index} className="flex flex-col md:flex-row items-center md:items-start text-center md:text-left space-y-4 md:space-y-0 md:space-x-6 relative">
                  {/* Vertical connection line for mobile */}
                  {index < steps.length - 1 && (
                    <div className="absolute left-1/2 md:left-8 top-16 w-0.5 h-12 bg-gradient-to-b from-indigo-500 to-purple-500 transform -translate-x-1/2 md:translate-x-0"></div>
                  )}
                  
                  <div className="flex-shrink-0">
                    <div className="w-16 h-16 bg-gradient-to-r from-indigo-600 to-purple-600 rounded-2xl flex items-center justify-center text-2xl font-bold shadow-lg shadow-indigo-500/25 relative z-10">
                      {step.number}
                    </div>
                  </div>
                  
                  <div className="flex-1">
                    <h3 className="text-xl font-bold mb-4 text-white">{step.title}</h3>
                    <p className="text-gray-400 leading-relaxed">{step.description}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* Transparency Demo Section */}
        <section className="py-24 px-4 bg-gradient-to-r from-indigo-900/20 to-purple-900/20 backdrop-blur-sm">
          <div className="max-w-6xl mx-auto">
            <div className="text-center mb-16">
              <h2 className="text-4xl md:text-5xl font-bold mb-6 bg-gradient-to-r from-white to-gray-300 bg-clip-text text-transparent">
                Complete Transparency
              </h2>
              <p className="text-xl text-gray-400 max-w-3xl mx-auto mb-12">
                Watch your AI team work in real-time with full visibility into every decision and process
              </p>
            </div>
            
            <div className="bg-gradient-to-br from-slate-900/80 to-slate-800/60 rounded-3xl p-8 border border-slate-700/50 backdrop-blur-sm">
              <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
                <div className="text-center">
                  <div className="w-12 h-12 bg-blue-500/20 rounded-xl flex items-center justify-center mx-auto mb-4">
                    <TransparencyIcon />
                  </div>
                  <h3 className="text-lg font-semibold text-white mb-2">Live Monitoring</h3>
                  <p className="text-gray-400 text-sm">Real-time visibility into AI agent activities and decisions</p>
                </div>
                <div className="text-center">
                  <div className="w-12 h-12 bg-green-500/20 rounded-xl flex items-center justify-center mx-auto mb-4">
                    <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6V4m0 2a2 2 0 100 4m0-4a2 2 0 110 4m-6 8a2 2 0 100-4m0 4a2 2 0 100 4m0-4a2 2 0 104 0m-4 0a2 2 0 104 0m6 0a2 2 0 100-4m0 4a2 2 0 100 4m0-4a2 2 0 104 0m-4 0a2 2 0 104 0" />
                    </svg>
                  </div>
                  <h3 className="text-lg font-semibold text-white mb-2">User Control</h3>
                  <p className="text-gray-400 text-sm">Pause, adjust, or override AI decisions at any time</p>
                </div>
                <div className="text-center">
                  <div className="w-12 h-12 bg-purple-500/20 rounded-xl flex items-center justify-center mx-auto mb-4">
                    <DataIcon />
                  </div>
                  <h3 className="text-lg font-semibold text-white mb-2">Performance Tracking</h3>
                  <p className="text-gray-400 text-sm">Detailed analytics on content performance and ROI</p>
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* Global Reach Section */}
        <section className="py-24 px-4">
          <div className="max-w-6xl mx-auto">
            <div className="text-center mb-16">
              <h2 className="text-4xl md:text-5xl font-bold mb-6 bg-gradient-to-r from-white to-gray-300 bg-clip-text text-transparent">
                Built for Global Markets
              </h2>
              <p className="text-xl text-gray-400 max-w-3xl mx-auto">
                Designed specifically for international businesses with multi-language and cross-cultural capabilities
              </p>
            </div>
            
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8">
              <div className="text-center p-6 rounded-2xl bg-gradient-to-br from-slate-900/50 to-slate-800/30 border border-slate-700/50">
                <div className="text-3xl mb-4">🌎</div>
                <h3 className="text-lg font-semibold text-white mb-2">Global Markets</h3>
                <p className="text-gray-400 text-sm">North America, Europe, Southeast Asia, Latin America</p>
              </div>
              <div className="text-center p-6 rounded-2xl bg-gradient-to-br from-slate-900/50 to-slate-800/30 border border-slate-700/50">
                <div className="text-3xl mb-4">🗣️</div>
                <h3 className="text-lg font-semibold text-white mb-2">7+ Languages</h3>
                <p className="text-gray-400 text-sm">English, Spanish, French, German, Japanese, Korean, Portuguese</p>
              </div>
              <div className="text-center p-6 rounded-2xl bg-gradient-to-br from-slate-900/50 to-slate-800/30 border border-slate-700/50">
                <div className="text-3xl mb-4">🎭</div>
                <h3 className="text-lg font-semibold text-white mb-2">Cultural Adaptation</h3>
                <p className="text-gray-400 text-sm">Content adapted for local customs and business environments</p>
              </div>
              <div className="text-center p-6 rounded-2xl bg-gradient-to-br from-slate-900/50 to-slate-800/30 border border-slate-700/50">
                <div className="text-3xl mb-4">⚡</div>
                <h3 className="text-lg font-semibold text-white mb-2">Real-time</h3>
                <p className="text-gray-400 text-sm">24/7 monitoring across all global time zones</p>
              </div>
            </div>
          </div>
        </section>

        {/* Final CTA Section */}
        <section className="py-24 px-4 bg-gradient-to-r from-indigo-900/30 to-purple-900/30 backdrop-blur-sm">
          <div className="max-w-4xl mx-auto text-center">
            <h2 className="text-4xl md:text-5xl font-bold mb-6 bg-gradient-to-r from-white to-gray-300 bg-clip-text text-transparent">
              Ready to Scale Your Global Content?
            </h2>
            <p className="text-xl text-gray-400 mb-8 leading-relaxed">
              Join international businesses using AI to create compelling content across cultures and languages
            </p>
            <p className="text-indigo-300 mb-12">
              Start with a free trial - no credit card required
            </p>
            
            <div className="flex flex-col sm:flex-row gap-4 justify-center items-center">
              <Button
                size="lg"
                onClick={handleGetStarted}
                disabled={isLoading}
                className="bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-700 hover:to-purple-700 text-lg px-8 py-6 rounded-xl transition-all duration-300 transform hover:scale-105 shadow-lg shadow-indigo-500/25"
              >
                {isLoading ? 'Loading...' : 'Start Free Trial'}
                <ArrowRightIcon />
              </Button>
              
              <Button
                size="lg"
                variant="outline"
                className="border-slate-600 bg-transparent text-white hover:bg-slate-800 text-lg px-8 py-6 rounded-xl transition-all duration-300"
              >
                Schedule Demo
              </Button>
            </div>
          </div>
        </section>

        {/* Footer */}
        <footer className="w-full py-12 border-t border-slate-800">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="flex flex-col md:flex-row justify-between items-center">
              <div className="flex items-center space-x-3 mb-4 md:mb-0">
                <div className="w-8 h-8 bg-gradient-to-r from-indigo-500 to-purple-600 rounded-lg flex items-center justify-center">
                  <span className="text-sm font-bold">M</span>
                </div>
                <span className="text-lg font-bold">Mercatus Content Factory</span>
              </div>
              <div className="text-center text-slate-500 text-sm">
                © {new Date().getFullYear()} Mercatus. All rights reserved. Built for global content creators.
              </div>
            </div>
          </div>
        </footer>
      </main>
    </div>
  );
}