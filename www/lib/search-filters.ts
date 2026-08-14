/** 홈 검색 필터(§3.1)의 URL 표현 — 홈 페이지와 빈 결과 안내(갭 #48)가 함께 쓴다. */

/** 가격대는 "하한-상한"(상한 없으면 생략) 한 파라미터로 URL에 실린다. */
export function parsePriceRange(price?: string): { price_min?: string; price_max?: string } {
  if (!price || !/^\d+-\d*$/.test(price)) return {};
  const [min, max] = price.split("-");
  return { price_min: min, ...(max ? { price_max: max } : {}) };
}

export type SearchFilters = {
  category?: string;
  q?: string;
  platform?: string;
  price?: string;
  location?: string;
};

/** 필터 → 홈 URL. 값이 없는 키는 빼서 기본 상태가 "/"로 수렴하게 한다. */
export function homeHref(filters: SearchFilters): string {
  const qs = new URLSearchParams(
    Object.entries(filters).filter(([, value]) => Boolean(value)) as [string, string][]
  ).toString();
  return qs ? `/?${qs}` : "/";
}

/** 필터 → 백엔드 목록 조회 쿼리(가격대는 min/max로 펼친다). */
export function listingQuery(filters: SearchFilters, extra: Record<string, string> = {}): string {
  return new URLSearchParams({
    ...extra,
    ...(filters.category ? { category: filters.category } : {}),
    ...(filters.q ? { q: filters.q } : {}),
    ...(filters.platform ? { platform: filters.platform } : {}),
    ...parsePriceRange(filters.price),
    ...(filters.location ? { location: filters.location } : {}),
  }).toString();
}
