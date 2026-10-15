import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

export function middleware(request: NextRequest) {
  const hasSessionCookie = Boolean(
    request.cookies.get("access_token")?.value || request.cookies.get("refresh_token")?.value,
  );

  if (!hasSessionCookie && request.nextUrl.pathname.startsWith("/workspace")) {
    const loginUrl = new URL("/login", request.url);
    loginUrl.searchParams.set("next", request.nextUrl.pathname);
    return NextResponse.redirect(loginUrl);
  }

  return NextResponse.next();
}

export const config = {
  matcher: ["/workspace/:path*"],
};
