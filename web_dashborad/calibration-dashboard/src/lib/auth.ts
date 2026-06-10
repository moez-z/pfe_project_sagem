import NextAuth from "next-auth";
import Credentials from "next-auth/providers/credentials";
import { prisma } from "@/lib/prisma";
import bcrypt from "bcryptjs";

export const { handlers, signIn, signOut, auth } = NextAuth({
  trustHost: true,
  session: { strategy: "jwt", maxAge: 2 * 60 * 60 },

  pages: { signIn: "/login" },
  callbacks: {
    async jwt({ token, user }) {
      if (user) {
        token.id = user.id;
        token.role = (user as any).role;
      }
      return token;
    },
    async session({ session, token }) {
      if (session.user) {
        (session.user as any).id = token.id;
        (session.user as any).role = token.role;
      }
      return session;
    },
  },
  providers: [
    Credentials({
      name: "Credentials",
      credentials: {
        matricule: { label: "Matricule", type: "text" },
        password: { label: "Password", type: "password" },
      },
      async authorize(credentials) {
        if (!credentials?.matricule || !credentials?.password) return null;
        const controller = new AbortController();
        const timeout = setTimeout(() => controller.abort(), 30000);
        try {
          const res = await fetch(
            `${process.env.NEXT_PUBLIC_API_URL}/auth/login`,
            {
              method: "POST",
              headers: { "Content-Type": "application/json" },
              body: JSON.stringify({
                matricule: credentials.matricule,
                password: credentials.password,
              }),
              signal: controller.signal,
            },
          );
          clearTimeout(timeout);

          if (!res.ok) return null;

          const user = await res.json();
          if (user.role?.toLowerCase() !== "admin") return null;

          return {
            id: String(user.id),
            name: user.full_name,
            email: user.matricule,
            role: user.role,
          };
        } catch {
          return null;
        }
      },
    }),
  ],
});
