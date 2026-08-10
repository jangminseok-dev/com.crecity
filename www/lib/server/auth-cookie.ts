// BFF(Route Handler) 전용 — 클라이언트 번들에 넣지 말 것.
import "server-only";

import type { NextResponse } from "next/server";

export { BACKEND_API_BASE } from "@/lib/server/backend-api";

export const REFRESH_COOKIE = "crecity_refresh";

// 백엔드 리프레시 TTL(14일, AUTH_REFRESH_TOKEN_TTL_SECONDS 기본값)과 맞춘다.
const REFRESH_COOKIE_MAX_AGE = 14 * 24 * 60 * 60;

export function setRefreshCookie(response: NextResponse, refreshToken: string): void {
  response.cookies.set(REFRESH_COOKIE, refreshToken, {
    httpOnly: true,
    sameSite: "lax",
    secure: process.env.NODE_ENV === "production",
    path: "/api/auth", // 인증 라우트에만 전송 — 다른 요청에 실려 다니지 않는다
    maxAge: REFRESH_COOKIE_MAX_AGE,
  });
}

export function clearRefreshCookie(response: NextResponse): void {
  response.cookies.set(REFRESH_COOKIE, "", { path: "/api/auth", maxAge: 0 });
}
