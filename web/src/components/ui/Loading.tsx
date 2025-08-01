import React from 'react';
import { cn } from '@/lib/utils';

export interface LoadingProps {
  type?: 'spinner' | 'dots' | 'pulse';
  size?: 'sm' | 'md' | 'lg';
  text?: string;
  className?: string;
}

const Loading: React.FC<LoadingProps> = ({
  type = 'spinner',
  size = 'md',
  text,
  className,
}) => {
  const sizes = {
    sm: 'h-4 w-4',
    md: 'h-8 w-8',
    lg: 'h-12 w-12',
  };

  const Spinner = () => (
    <svg
      className={cn('animate-spin', sizes[size])}
      xmlns="http://www.w3.org/2000/svg"
      fill="none"
      viewBox="0 0 24 24"
    >
      <circle
        className="opacity-25"
        cx="12"
        cy="12"
        r="10"
        stroke="currentColor"
        strokeWidth="4"
      />
      <path
        className="opacity-75"
        fill="currentColor"
        d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
      />
    </svg>
  );

  const Dots = () => (
    <div className="flex space-x-1">
      <div className={cn('animate-bounce bg-current rounded-full', sizes[size])} style={{ animationDelay: '0ms' }} />
      <div className={cn('animate-bounce bg-current rounded-full', sizes[size])} style={{ animationDelay: '150ms' }} />
      <div className={cn('animate-bounce bg-current rounded-full', sizes[size])} style={{ animationDelay: '300ms' }} />
    </div>
  );

  const Pulse = () => (
    <div className={cn('animate-pulse bg-current rounded-full', sizes[size])} />
  );

  const renderLoader = () => {
    switch (type) {
      case 'dots':
        return <Dots />;
      case 'pulse':
        return <Pulse />;
      default:
        return <Spinner />;
    }
  };

  return (
    <div className={cn('flex flex-col items-center justify-center', className)}>
      <div className="text-blue-600">
        {renderLoader()}
      </div>
      {text && (
        <p className="mt-2 text-sm text-gray-600">{text}</p>
      )}
    </div>
  );
};

export { Loading }; 