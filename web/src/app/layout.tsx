import type { Metadata } from 'next';
import { Inter } from 'next/font/google';
import './globals.css';
import AppLayout from "@/components/layout/AppLayout";
import SessionProvider from "@/components/layout/SessionProvider";
import SWRProvider from "@/components/layout/SWRProvider";
import { NextIntlClientProvider } from 'next-intl';
import { getMessages } from 'next-intl/server';

const inter = Inter({ subsets: ['latin'] });

export const metadata: Metadata = {
  title: 'Mercatus',
  description: 'AI-Powered Multi-Agent Task Management Platform',
  icons: {
    icon: [
      { url: '/favicon.svg', type: 'image/svg+xml' },
      { url: '/favicon.ico', type: 'image/x-icon', sizes: '32x32' }
    ],
    shortcut: '/favicon.svg',
    apple: '/favicon.svg',
  },
};

export default async function RootLayout({
  children,
  params: { locale }
}: {
  children: React.ReactNode;
  params: { locale: string };
}) {
  const messages = await getMessages();
  return (
    <html lang={locale}>
      <body className={inter.className}>
        <SessionProvider>
          <SWRProvider>
            <NextIntlClientProvider locale={locale} messages={messages}>
              <AppLayout>{children}</AppLayout>
            </NextIntlClientProvider>
          </SWRProvider>
        </SessionProvider>
      </body>
    </html>
  );
} 