import { NextResponse } from "next/server";

import { clearRefreshCookie } from "@/lib/server/auth-cookie";

/** 로그아웃 BFF — 리프레시 쿠키 삭제. (백엔드 측 토큰 폐기 엔드포인트 도입 시 호출 추가) */
export async function POST() {
  const response = new NextResponse(null, { status: 204 });
  clearRefreshCookie(response);
  return response;
}
