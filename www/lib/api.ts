import { useAuthStore } from "@/lib/auth-store";

// 브라우저 fetch는 절대 URL 금지 — /api/backend rewrite 경유(루트 CLAUDE.md 규칙).
const API_BASE = "/api/backend";

export class ApiError extends Error {
  constructor(
    public readonly status: number,
    public readonly detail: string,
  ) {
    super(detail);
  }
}

// 401 동시 다발 시 갱신 요청은 한 번만 나가도록 in-flight 프로미스를 공유한다.
let refreshing: Promise<boolean> | null = null;

export async function refreshSession(): Promise<boolean> {
  refreshing ??= (async () => {
    try {
      const res = await fetch("/api/auth/refresh", { method: "POST" });
      if (!res.ok) {
        useAuthStore.getState().clearSession();
        return false;
      }
      const { access_token } = (await res.json()) as { access_token: string };
      useAuthStore.getState().setSession(access_token);
      return true;
    } catch {
      useAuthStore.getState().clearSession();
      return false;
    } finally {
      refreshing = null;
    }
  })();
  return refreshing;
}

async function request(path: string, init: RequestInit): Promise<Response> {
  const accessToken = useAuthStore.getState().accessToken;
  return fetch(`${API_BASE}${path}`, {
    ...init,
    headers: {
      // FormData는 브라우저가 boundary 포함 Content-Type을 직접 붙인다
      ...(init.body && !(init.body instanceof FormData)
        ? { "Content-Type": "application/json" }
        : {}),
      ...(accessToken ? { Authorization: `Bearer ${accessToken}` } : {}),
      ...init.headers,
    },
  });
}

/** 백엔드 호출 공용 래퍼 — 401이면 리프레시 회전 후 1회 재시도한다. */
export async function apiFetch<T>(path: string, init: RequestInit = {}): Promise<T> {
  let res = await request(path, init);
  if (res.status === 401 && (await refreshSession())) {
    res = await request(path, init);
  }
  if (!res.ok) {
    const body = (await res.json().catch(() => null)) as { detail?: unknown } | null;
    const detail = typeof body?.detail === "string" ? body.detail : `요청 실패 (${res.status})`;
    throw new ApiError(res.status, detail);
  }
  if (res.status === 204) return undefined as T;
  return (await res.json()) as T;
}
