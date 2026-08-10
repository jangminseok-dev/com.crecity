// 서버 컴포넌트·Route Handler 전용 — 백엔드를 직접 부른다(rewrite는 브라우저용).
import "server-only";

// next.config.ts rewrite와 같은 기준.
export const BACKEND_API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://127.0.0.1:8000";

/** 공개 데이터 GET — 404는 null, 그 외 실패는 throw. SSR 페이지는 항상 신선한 데이터를 쓴다. */
export async function backendGet<T>(path: string): Promise<T | null> {
  const res = await fetch(`${BACKEND_API_BASE}${path}`, { cache: "no-store" });
  if (res.status === 404) return null;
  if (!res.ok) throw new Error(`백엔드 요청 실패: ${path} (${res.status})`);
  return (await res.json()) as T;
}
