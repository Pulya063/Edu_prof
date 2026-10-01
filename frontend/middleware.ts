import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

export function middleware(request: NextRequest) {
  const token = request.cookies.get("access_token")?.value;
  
  if (!token && request.nextUrl.pathname.startsWith("/workspace")) {
    return NextResponse.redirect(new URL("/login", request.url));
  }
  
  // If user is already logged in and tries to access login/register, redirect to workspace
  if (token && (request.nextUrl.pathname.startsWith("/login") || request.nextUrl.pathname.startsWith("/register"))) {
    return NextResponse.redirect(new URL("/workspace/overview", request.url));
  }

  return NextResponse.next();
}

export const config = {
  matcher: ["/workspace/:path*", "/login", "/register"],
};
