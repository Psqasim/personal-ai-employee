import { auth } from "@/auth";
import { NextResponse } from "next/server";

// Force Node.js runtime to avoid Edge Runtime restrictions
export const runtime = "nodejs";

export default auth((req) => {
  const { pathname } = req.nextUrl;

  // Public routes
  if (pathname === "/login" || pathname.startsWith("/api/auth")) {
    return NextResponse.next();
  }

  // Protected routes - require authentication
  if (!req.auth && pathname.startsWith("/dashboard")) {
    const loginUrl = new URL("/login", req.url);
    loginUrl.searchParams.set("callbackUrl", pathname);
    return NextResponse.redirect(loginUrl);
  }

  // Check admin-only routes
  const adminOnlyPaths = ["/dashboard/settings", "/api/users"];
  const isAdminPath = adminOnlyPaths.some((path) => pathname.startsWith(path));

  if (isAdminPath && req.auth?.user) {
    const userRole = (req.auth.user as any).role;
    if (userRole !== "admin") {
      return NextResponse.redirect(new URL("/dashboard", req.url));
    }
  }

  return NextResponse.next();
});

export const config = {
  matcher: ["/((?!api|_next/static|_next/image|favicon.ico).*)"],
};
