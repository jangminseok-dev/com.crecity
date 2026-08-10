import { NextRequest, NextResponse } from "next/server";

import {
  BACKEND_API_BASE,
  REFRESH_COOKIE,
  clearRefreshCookie,
  setRefreshCookie,
} from "@/lib/server/auth-cookie";

/** 토큰 갱신 BFF — 쿠키의 리프레시 토큰을 회전(1회용)시키고 새 액세스 토큰을 돌려준다. */
export async function POST(request: NextRequest) {
  const refreshToken = request.cookies.get(REFRESH_COOKIE)?.value;
  if (!refreshToken) {
    return NextResponse.json({ detail: "로그인이 필요합니다." }, { status: 401 });
  }
  const backendResponse = await fetch(`${BACKEND_API_BASE}/auth/tokens/refresh`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ refresh_token: refreshToken }),
  });
  const payload = await backendResponse.json();
  if (!backendResponse.ok) {
    const response = NextResponse.json(payload, { status: backendResponse.status });
    clearRefreshCookie(response); // 무효 토큰은 쿠키도 버린다
    return response;
  }
  const { access_token, refresh_token } = payload as {
    access_token: string;
    refresh_token: string;
  };
  const response = NextResponse.json({ access_token });
  setRefreshCookie(response, refresh_token);
  return response;
}
