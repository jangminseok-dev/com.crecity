// 세션 사용자 — 액세스 토큰(JWT) 페이로드에서 읽는다. 서명 검증은 백엔드 몫이고
// 프론트는 표시 용도로만 디코드한다.
export type SessionUser = {
  id: number;
  email: string;
  account_type: "CREATOR" | "BRAND";
};

export function decodeSessionUser(accessToken: string): SessionUser | null {
  const payload = accessToken.split(".")[1];
  if (!payload) return null;
  try {
    const base64 = payload.replace(/-/g, "+").replace(/_/g, "/");
    const bytes = Uint8Array.from(atob(base64), (c) => c.charCodeAt(0));
    const claims = JSON.parse(new TextDecoder().decode(bytes)) as {
      sub: string;
      email: string;
      account_type: SessionUser["account_type"];
    };
    return { id: Number(claims.sub), email: claims.email, account_type: claims.account_type };
  } catch {
    return null;
  }
}
