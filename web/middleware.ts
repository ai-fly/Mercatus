import { NextRequest, NextResponse } from 'next/server';
import createMiddleware from 'next-intl/middleware';
import { locales, defaultLocale } from './src/i18n/config';

// 1️⃣ Base next-intl middleware (cookie-based, no URL prefix)
const intlMiddleware = createMiddleware({
  locales,
  defaultLocale,
  localePrefix: 'never'
});

// 2️⃣ Wrapper to handle legacy prefixes and root path
export default function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl;

  // Don't redirect root path - let the root page handle language selection
  if (pathname === '/') {
    return NextResponse.next();
  }

  // Handle legacy locale prefixes: strip them
  const prefixRegex = new RegExp(`^/(${locales.join('|')})(/|$)`, 'i');
  if (prefixRegex.test(pathname)) {
    const newPath = pathname.replace(prefixRegex, '/');
    const url = request.nextUrl.clone();
    url.pathname = newPath.startsWith('/') ? newPath : `/${newPath}`;
    return NextResponse.redirect(url, 307);
  }

  // Otherwise, continue with regular i18n handling
  return intlMiddleware(request);
}

export const config = {
  // Run on all application routes (skip _next, static files etc.) so that un-prefixed
  // URLs like "/dashboard" are handled correctly when the locale lives in a cookie
  matcher: ['/', '/((?!api|_next|.*\\..*).*)']
}; 