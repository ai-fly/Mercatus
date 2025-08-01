import React from 'react';

export const LoginBanner = () => {
  return (
    <div className="relative w-full h-80 mt-4">
      <svg
        width="100%"
        height="100%"
        viewBox="0 0 400 300"
        preserveAspectRatio="xMidYMid meet"
        className="absolute inset-0"
      >
        <defs>
          <radialGradient id="grad-blue" cx="50%" cy="50%" r="50%" fx="50%" fy="50%">
            <stop offset="0%" style={{ stopColor: 'rgba(59, 130, 246, 0.4)', stopOpacity: 1 }} />
            <stop offset="100%" style={{ stopColor: 'rgba(59, 130, 246, 0)', stopOpacity: 0 }} />
          </radialGradient>
          <radialGradient id="grad-indigo" cx="50%" cy="50%" r="50%" fx="50%" fy="50%">
            <stop offset="0%" style={{ stopColor: 'rgba(129, 140, 248, 0.3)', stopOpacity: 1 }} />
            <stop offset="100%" style={{ stopColor: 'rgba(129, 140, 248, 0)', stopOpacity: 0 }} />
          </radialGradient>
          <linearGradient id="line-grad" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" style={{ stopColor: 'rgba(99, 102, 241, 1)' }} />
            <stop offset="100%" style={{ stopColor: 'rgba(59, 130, 246, 1)' }} />
          </linearGradient>
        </defs>

        {/* Background Glows */}
        <circle cx="100" cy="150" r="100" fill="url(#grad-blue)" />
        <circle cx="300" cy="150" r="80" fill="url(#grad-indigo)" />

        {/* Neural Network Lines */}
        <path d="M 50 150 Q 150 50 250 150 T 350 150" stroke="url(#line-grad)" strokeWidth="2" fill="none" strokeDasharray="5 5">
          <animate attributeName="stroke-dashoffset" from="10" to="0" dur="2s" repeatCount="indefinite" />
        </path>
        <path d="M 50 150 Q 150 250 250 150" stroke="url(#line-grad)" strokeWidth="1.5" fill="none" opacity="0.7" />
        <path d="M 80 100 Q 180 180 280 100" stroke="url(#line-grad)" strokeWidth="1" fill="none" opacity="0.5" />
        <path d="M 80 200 Q 180 120 280 200" stroke="url(#line-grad)" strokeWidth="1" fill="none" opacity="0.5" />

        {/* Nodes */}
        {[
          { cx: 50, cy: 150 }, { cx: 250, cy: 150 }, { cx: 350, cy: 150 },
          { cx: 80, cy: 100 }, { cx: 280, cy: 100 },
          { cx: 80, cy: 200 }, { cx: 280, cy: 200 },
          { cx: 150, cy: 50 }, { cx: 150, cy: 250 },
        ].map((node, i) => (
          <circle key={i} cx={node.cx} cy={node.cy} r="4" fill="white">
            <animate attributeName="r" values="4;6;4" dur="3s" repeatCount="indefinite" begin={`${i * 0.2}s`} />
          </circle>
        ))}
      </svg>
    </div>
  );
}; 