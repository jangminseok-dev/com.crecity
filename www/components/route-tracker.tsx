"use client";

import { usePathname } from "next/navigation";
import { useEffect } from "react";

import { rememberReturnPath } from "@/lib/oauth";

/**
 * 로그인 후 원래 페이지 복귀(갭 #94) — 화면 이동마다 마지막 경로를 기억해 두면
 * 어디서 로그인에 들어와도(헤더·구매 유도·직접 입력) OAuth 콜백이 그리로 되돌린다.
 * 로그인·콜백 화면 자체는 복귀 대상이 아니므로 기록하지 않는다.
 */
export default function RouteTracker() {
  const pathname = usePathname();

  useEffect(() => {
    if (pathname.startsWith("/login") || pathname.startsWith("/oauth")) return;
    // 쿼리까지 보존해야 "이 패키지 주문" 같은 상태가 살아난다(usePathname에는 쿼리가 없다)
    rememberReturnPath(pathname + window.location.search);
  }, [pathname]);

  return null;
}
