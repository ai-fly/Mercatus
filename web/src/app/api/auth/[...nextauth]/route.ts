import NextAuth, { AuthOptions } from "next-auth";
import GoogleProvider from "next-auth/providers/google";

export const authOptions: AuthOptions = {
  providers: [
    GoogleProvider({
      clientId: process.env.GOOGLE_CLIENT_ID as string,
      clientSecret: process.env.GOOGLE_CLIENT_SECRET as string,
    }),
  ],
  callbacks: {
    async jwt({ token, account, profile }) {
      // On initial sign-in, account object is available.
      // We exchange the Google id_token for a token from our own backend.
      if (account?.id_token) {
        try {
          // On the first sign-in, user details are in the `profile` object.
          const response = await fetch(`${process.env.BACKEND_API_URL}/api/v1/auth/google/login`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              id_token: account.id_token, 
              profile: {
                email: profile?.email,
                name: profile?.name,
                picture: token?.picture,
                // These are Google-specific and might be in profile
                given_name: token?.given_name,
                family_name: token?.family_name,
              },
            }),
          });

          if (!response.ok) {
            const errorText = await response.text();
            console.error('Failed to exchange token with backend:', response.status, errorText);
            throw new Error('Backend token exchange failed');
          }

          const { access_token } = await response.json();
          token.backendToken = access_token; // Store your backend's token
        } catch (error) {
          console.error('Error during token exchange:', error);
          // Add an error property to the token to indicate failure
          return { ...token, error: "TokenExchangeError" };
        }
      }
      return token;
    },

    async session({ session, token }) {
      // Make the backend token available in the client-side session object.
      session.backendToken = token.backendToken as string;

      // The original Google tokens are no longer needed in the session.
      // @ts-expect-error: accessToken is not defined in the Session type but may exist at runtime
      delete session.accessToken;
      // @ts-expect-error: idToken is not defined in the Session type but may exist at runtime
      delete session.idToken;

      return session;
    },
  },
  secret: process.env.NEXTAUTH_SECRET,
};

const handler = NextAuth(authOptions);

export { handler as GET, handler as POST }; 