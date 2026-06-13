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

        try {
          console.log("[AUTH] Calling API:", process.env.API_URL);
          const res = await fetch(`${process.env.API_URL}/auth/login`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
              matricule: credentials.matricule,
              password: credentials.password,
            }),
          });

          console.log("[AUTH] Response status:", res.status);
          const data = await res.json();
          console.log("[AUTH] Response data:", JSON.stringify(data));

          if (!res.ok) return null;
          if (data.role?.toLowerCase() !== "admin") return null;

          return {
            id: String(data.id),
            name: data.full_name,
            matricule: data.matricule,
            role: data.role,
          };
        } catch (e) {
          console.error("[AUTH] Error:", e);
          return null;
        }
      },
    }),
  ],
});
