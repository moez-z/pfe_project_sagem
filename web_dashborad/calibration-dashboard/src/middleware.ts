import { NextRequest, NextResponse } from "next/server";
import { getToken } from "next-auth/jwt";

export async function middleware(req: NextRequest) {
  const { pathname } = req.nextUrl;

  const token = await getToken({
    req,
    secret: process.env.AUTH_SECRET,
  });

  console.log("[MIDDLEWARE] Path:", pathname);
  console.log("[MIDDLEWARE] Token:", JSON.stringify(token));
  console.log("[MIDDLEWARE] AUTH_SECRET exists:", !!process.env.AUTH_SECRET);

  const isLoggedIn = !!token;
  const isAdmin = (token?.role as string)?.toLowerCase() === "admin";

  if (pathname.startsWith("/dashboard")) {
    if (!isLoggedIn) return NextResponse.redirect(new URL("/login", req.url));
    if (!isAdmin)
      return NextResponse.redirect(
        new URL("/login?error=unauthorized", req.url),
      );
  }

  if (pathname === "/login" && isLoggedIn && isAdmin)
    return NextResponse.redirect(new URL("/dashboard", req.url));

  return NextResponse.next();
}

export const config = {
  matcher: ["/dashboard/:path*", "/login"],
};
