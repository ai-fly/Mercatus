'use client';

import React from 'react';
import { useLocale } from 'next-intl';
import { Button } from './Button';
import { ChevronDown } from 'lucide-react';

export interface LanguageSwitcherProps {
  className?: string;
  variant?: 'button' | 'dropdown';
}

const LanguageSwitcher: React.FC<LanguageSwitcherProps> = ({
  className,
  variant = 'dropdown',
}) => {
  const locale = useLocale();

  const languages = [
    { code: 'zh', name: '中文', flag: '🇨🇳' },
    { code: 'en', name: 'English', flag: '🇺🇸' },
  ];

  const currentLanguage = languages.find(lang => lang.code === locale);

  const handleLanguageChange = (newLocale: string) => {
    document.cookie = `NEXT_LOCALE=${newLocale}; path=/; max-age=31536000; samesite=lax`;
    window.location.reload();
  };

  if (variant === 'dropdown') {
    return (
      <div className={`relative group ${className}`}>
        <Button
          variant="ghost"
          size="sm"
          className="flex items-center space-x-2 text-white"
        >
          <span>{currentLanguage?.flag}</span>
          <ChevronDown className="w-4 h-4" />
        </Button>
        
        <div className="absolute right-0 mt-2 w-40 bg-gray-800 rounded-md shadow-lg border border-gray-700 opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all duration-200 z-50">
          <div className="py-1">
            {languages.map((language) => (
              <button
                key={language.code}
                onClick={() => handleLanguageChange(language.code)}
                className={`w-full flex items-center px-4 py-2 text-sm transition-colors ${
                  locale === language.code
                    ? 'bg-blue-500 text-white'
                    : 'text-gray-300 hover:bg-gray-700 hover:text-white'
                }`}
              >
                <span className="mr-3">{language.flag}</span>
                {language.name}
              </button>
            ))}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className={`flex space-x-2 ${className}`}>
      {languages.map((language) => (
        <Button
          key={language.code}
          variant={locale === language.code ? 'primary' : 'ghost'}
          size="sm"
          className="flex items-center space-x-1"
          onClick={() => handleLanguageChange(language.code)}
        >
          <span>{language.flag}</span>
          <span>{language.name}</span>
        </Button>
      ))}
    </div>
  );
};

export { LanguageSwitcher }; 