"use client";

import { useEffect } from "react";

import { refreshSession } from "@/lib/api";

/** 앱 시작 시 httpOnly 쿠키의 리프레시 토큰으로 세션을 복원한다(실패하면 guest). */
export default function AuthSessionProvider({ children }: { children: React.ReactNode }) {
  useEffect(() => {
    void refreshSession();
  }, []);
  return children;
}
