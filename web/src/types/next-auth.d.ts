import "next-auth";

declare module "next-auth" {
  interface Session {
    // This is the token from your own backend.
    backendToken?: string;
    user?: {
      id?: string | null;
      name?: string | null;
      email?: string | null;
      image?: string | null;
    };
  }
}

declare module "next-auth/jwt" {
  interface JWT {
    // This is the token from your own backend.
    backendToken?: string;
  }
} 