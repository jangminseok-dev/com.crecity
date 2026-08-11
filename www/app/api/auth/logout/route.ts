import { NextRequest, NextResponse } from "next/server";

import { BACKEND_API_BASE, REFRESH_COOKIE, clearRefreshCookie } from "@/lib/server/auth-cookie";

/** 로그아웃 BFF — 백엔드 리프레시 토큰 폐기 후 쿠키 삭제. */
export async function POST(request: NextRequest) {
  const refreshToken = request.cookies.get(REFRESH_COOKIE)?.value;
  if (refreshToken) {
    // 폐기는 멱등(204) — 실패해도 로그아웃 자체(쿠키 삭제)는 진행한다
    try {
      await fetch(`${BACKEND_API_BASE}/auth/tokens/logout`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ refresh_token: refreshToken }),
      });
    } catch {
      // 백엔드 불통 시에도 클라이언트 세션은 끊는다 — 토큰은 TTL로 소멸
    }
  }
  const response = new NextResponse(null, { status: 204 });
  clearRefreshCookie(response);
  return response;
}
