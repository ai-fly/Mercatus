import { getRequestConfig } from 'next-intl/server';
import { locales, defaultLocale } from './config';
import { hasLocale } from 'next-intl';

export default getRequestConfig(async ({ requestLocale }) => {
  const locale = hasLocale(locales, requestLocale) ? requestLocale : defaultLocale;
  return {
    locale,
    messages: (await import(`../messages/${locale}.json`)).default
  };
}); 