This is a [Next.js](https://nextjs.org) project bootstrapped with [`create-next-app`](https://nextjs.org/docs/app/api-reference/cli/create-next-app).

## Getting Started

First, run the development server:

```bash
npm run dev
# or
yarn dev
# or
pnpm dev
# or
bun dev
```

Open [http://localhost:3000](http://localhost:3000) with your browser to see the result.

You can start editing the page by modifying `app/page.tsx`. The page auto-updates as you edit the file.

This project uses [`next/font`](https://nextjs.org/docs/app/building-your-application/optimizing/fonts) to automatically optimize and load [Geist](https://vercel.com/font), a new font family for Vercel.

## Learn More

To learn more about Next.js, take a look at the following resources:

- [Next.js Documentation](https://nextjs.org/docs) - learn about Next.js features and API.
- [Learn Next.js](https://nextjs.org/learn) - an interactive Next.js tutorial.

You can check out [the Next.js GitHub repository](https://github.com/vercel/next.js) - your feedback and contributions are welcome!

## Deploy on Vercel

The easiest way to deploy your Next.js app is to use the [Vercel Platform](https://vercel.com/new?utm_medium=default-template&filter=next.js&utm_source=create-next-app&utm_campaign=create-next-app-readme) from the creators of Next.js.

Check out our [Next.js deployment documentation](https://nextjs.org/docs/app/building-your-application/deploying) for more details.

## Google OAuth Setup

To enable Google Sign-In on the **Login** page you must provide a public OAuth client ID.

1. Create a project in the [Google Cloud Console](https://console.cloud.google.com/) and enable the **OAuth 2.0 Client IDs** credential.
2. Add `http://localhost:3000` (or your deployed origin) to the **Authorised JavaScript origins** list.
3. Add `http://localhost:3000/auth/callback` (or your deployed callback) to the **Authorised redirect URIs** list.
4. Copy the *Client ID* value.
5. Create a `.env.local` file in the project root and add:

```bash
NEXT_PUBLIC_GOOGLE_CLIENT_ID=<YOUR_CLIENT_ID_HERE>
```

6. Restart the dev server so Next.js can pick up the new environment variable.

The login page will now show a **Sign in with Google** button that uses the [Google Identity Services](https://developers.google.com/identity/gsi/web) SDK under the hood.

## 🏠 Home Page

The landing page has been redesigned with a clean, tech-oriented hero section and a concise feature showcase.

### Vision

> "Unleash AI to redefine the future of content marketing."  
> – Mercatus Content Factory

### Key Features

1. **Intelligent Planning** – Generate multi-channel marketing plans in one click.
2. **Automated Execution** – Collaborative expert agents create, publish and promote content automatically.
3. **Real-time Analytics** – Full-funnel performance monitoring and insights.

The page is fully internationalized (🇨🇳 / 🇺🇸) and built with Tailwind CSS, delivering a futuristic, immersive experience.

## 🌐 Internationalization Update (2025-07-20)

The application now stores the user's language preference in a cookie rather than in the URL path.
- URLs like `/dashboard` or `/settings` are now language-agnostic—no more `/en/dashboard`.
- The middleware detects the locale using (in order): the `NEXT_LOCALE` cookie, the browser's `Accept-Language` header, or the default locale (`zh`).
- Language switching is now purely cookie-based: clicking a language flag sets the `NEXT_LOCALE` cookie and refreshes the page to apply the new locale without any URL changes.

Technical details:
1. `middleware.ts` is configured with `localePrefix: 'never'` so no language prefix appears in routes.
2. A universal matcher ensures the middleware runs for every app route.
3. The `LanguageSwitcher` component now uses `document.cookie` to set the `NEXT_LOCALE` cookie and `window.location.reload()` to apply changes.
4. Navigation helpers (`Link`, `useRouter`, etc.) are created with the same strategy, so generated links stay prefix-free.

Legacy safety: old links containing `/zh` or `/en` now 307-redirect to the clean path automatically (handled in `middleware.ts`).  
This keeps links clean, backwards-compatible, and SEO-friendly while still allowing full i18n support.
