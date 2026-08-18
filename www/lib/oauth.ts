// OAuth 인가 요청 컨텍스트 — 콜백에서 state 검증·계정 유형 복원에 쓴다.
// sessionStorage: 탭 단위·닫으면 소멸(토큰이 아니라 1회용 CSRF 컨텍스트만 담는다).
const STORAGE_KEY = "crecity_oauth";
const RETURN_KEY = "crecity_return_path";

export type OAuthContext = {
  provider: "naver" | "google";
  state: string;
  account_type: "CREATOR" | "BRAND";
  return_to?: string; // 로그인 전에 보던 페이지(갭 #94) — 콜백이 복원한다
};

/** 로그인 전 마지막 경로 기록(갭 #94) — RouteTracker가 화면 이동마다 호출한다. */
export function rememberReturnPath(path: string): void {
  sessionStorage.setItem(RETURN_KEY, path);
}

/** 기록된 복귀 경로 — 같은 오리진 경로("/...")만 신뢰한다(오픈 리다이렉트 방지). */
function storedReturnPath(): string | undefined {
  const path = sessionStorage.getItem(RETURN_KEY);
  return path && path.startsWith("/") && !path.startsWith("//") ? path : undefined;
}

export function createOAuthContext(
  provider: OAuthContext["provider"],
  account_type: OAuthContext["account_type"],
): OAuthContext {
  const state = crypto.randomUUID();
  // OAuth는 외부 사이트를 왕복하므로 복귀 경로를 쿼리가 아니라 컨텍스트에 함께 싣는다
  const context: OAuthContext = { provider, state, account_type, return_to: storedReturnPath() };
  sessionStorage.setItem(STORAGE_KEY, JSON.stringify(context));
  return context;
}

export function consumeOAuthContext(): OAuthContext | null {
  const raw = sessionStorage.getItem(STORAGE_KEY);
  sessionStorage.removeItem(STORAGE_KEY); // 1회용
  if (!raw) return null;
  try {
    return JSON.parse(raw) as OAuthContext;
  } catch {
    return null;
  }
}

export function oauthRedirectUri(provider: string): string {
  return `${window.location.origin}/oauth/${provider}/callback`;
}
