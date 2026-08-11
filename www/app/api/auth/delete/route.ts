import { NextRequest, NextResponse } from "next/server";

import { BACKEND_API_BASE, REFRESH_COOKIE, clearRefreshCookie } from "@/lib/server/auth-cookie";

/** 계정 삭제 BFF — 액세스 토큰으로 백엔드 탈퇴를 호출하고, 성공 시 리프레시 쿠키도 지운다. */
export async function POST(request: NextRequest) {
  const accessToken = request.headers.get("authorization");
  if (!accessToken) {
    return NextResponse.json({ detail: "로그인이 필요합니다." }, { status: 401 });
  }
  const backendResponse = await fetch(`${BACKEND_API_BASE}/auth/account/delete`, {
    method: "POST",
    headers: { "Content-Type": "application/json", Authorization: accessToken },
    // 리프레시 토큰까지 함께 폐기 — 탈퇴 후 갱신으로 되살아나지 않게
    body: JSON.stringify({ refresh_token: request.cookies.get(REFRESH_COOKIE)?.value ?? "" }),
  });
  if (!backendResponse.ok) {
    const payload = await backendResponse.json().catch(() => ({ detail: "탈퇴에 실패했습니다." }));
    return NextResponse.json(payload, { status: backendResponse.status });
  }
  const response = new NextResponse(null, { status: 204 });
  clearRefreshCookie(response);
  return response;
}
