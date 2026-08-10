import { create } from "zustand";

import { decodeSessionUser, type SessionUser } from "@/lib/session";

// 액세스 토큰은 메모리에만 둔다(localStorage 금지 — XSS 보호).
// 리프레시 토큰은 httpOnly 쿠키(/api/auth Route Handler 전용)라 JS에서 보이지 않는다.
type AuthState = {
  status: "loading" | "guest" | "authenticated";
  accessToken: string | null;
  user: SessionUser | null;
  setSession: (accessToken: string) => void;
  clearSession: () => void;
};

export const useAuthStore = create<AuthState>((set) => ({
  status: "loading",
  accessToken: null,
  user: null,
  setSession: (accessToken) =>
    set({ status: "authenticated", accessToken, user: decodeSessionUser(accessToken) }),
  clearSession: () => set({ status: "guest", accessToken: null, user: null }),
}));
