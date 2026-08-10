// OAuth 인가 요청 컨텍스트 — 콜백에서 state 검증·계정 유형 복원에 쓴다.
// sessionStorage: 탭 단위·닫으면 소멸(토큰이 아니라 1회용 CSRF 컨텍스트만 담는다).
const STORAGE_KEY = "crecity_oauth";

export type OAuthContext = {
  provider: "naver" | "google";
  state: string;
  account_type: "CREATOR" | "BRAND";
};

export function createOAuthContext(
  provider: OAuthContext["provider"],
  account_type: OAuthContext["account_type"],
): OAuthContext {
  const state = crypto.randomUUID();
  const context: OAuthContext = { provider, state, account_type };
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
