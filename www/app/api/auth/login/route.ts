import { NextRequest, NextResponse } from "next/server";

import { BACKEND_API_BASE, setRefreshCookie } from "@/lib/server/auth-cookie";

type LoginRequestBody = {
  provider: "kakao" | "naver" | "google";
  code: string;
  redirect_uri: string;
  state: string;
  account_type: "CREATOR" | "BRAND";
};

type BackendLoginResponse = {
  access_token: string;
  refresh_token: string;
  token_type: string;
  is_new_user: boolean;
  user: { id: number; email: string; name: string; account_type: string };
};

/** 소셜 로그인 BFF — 백엔드 토큰 쌍을 받아 리프레시는 httpOnly 쿠키로 격리한다. */
export async function POST(request: NextRequest) {
  const body = (await request.json()) as LoginRequestBody;
  const backendResponse = await fetch(
    `${BACKEND_API_BASE}/auth/social/${body.provider}/login`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        code: body.code,
        redirect_uri: body.redirect_uri,
        state: body.state,
        account_type: body.account_type,
      }),
    },
  );
  const payload = await backendResponse.json();
  if (!backendResponse.ok) {
    return NextResponse.json(payload, { status: backendResponse.status });
  }
  const { refresh_token, ...rest } = payload as BackendLoginResponse;
  const response = NextResponse.json(rest); // refresh_token은 응답 본문에서 제거
  setRefreshCookie(response, refresh_token);
  return response;
}
