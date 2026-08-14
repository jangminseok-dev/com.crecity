/**
 * 단가 추정 로직(§3.9 무료 도구) — 공개 계산기와 크리에이터 단가 도우미(갭 #51)가 공유한다.
 *
 * 기준 단가는 **시장 참고치**다. 실거래가가 쌓이면 보정한다(launch-checklist §3).
 */

/* 플랫폼별 팔로워 1명당 기본 단가(원) — 국내 시장 통상 범위의 중간값 참고치 */
export const PLATFORM_RATES: { value: string; label: string; perFollower: number }[] = [
  { value: "INSTAGRAM", label: "인스타그램 (릴스·피드)", perFollower: 15 },
  { value: "YOUTUBE", label: "유튜브 (영상 1편)", perFollower: 40 },
  { value: "TIKTOK", label: "틱톡 (영상 1편)", perFollower: 12 },
  { value: "NAVER_BLOG", label: "네이버 블로그 (포스팅 1건)", perFollower: 10 },
];

/* 참여율 구간별 보정 — 참여가 높을수록 단가가 올라간다 */
export function engagementMultiplier(engagementRate: number): number {
  if (engagementRate <= 0) return 1;
  if (engagementRate < 1) return 0.7;
  if (engagementRate < 3) return 1;
  if (engagementRate < 6) return 1.3;
  return 1.6;
}

export type Estimate = { low: number; high: number; platformLabel: string };

/**
 * 팔로워·참여율(%)로 협상 폭 ±30%의 단가 범위를 만든다.
 * 대상 플랫폼이 없거나 팔로워가 0 이하면 null(UGC처럼 팔로워와 무관한 상품 포함).
 */
export function estimatePrice(
  platformValue: string,
  followers: number,
  engagementRate: number
): Estimate | null {
  const platform = PLATFORM_RATES.find((item) => item.value === platformValue);
  if (!platform || !followers || followers <= 0) return null;

  const base = followers * platform.perFollower * engagementMultiplier(engagementRate);
  // 만 원 단위 반올림 — 최소 1만 원
  const round = (value: number) => Math.max(10000, Math.round(value / 10000) * 10000);
  return {
    low: round(base * 0.7),
    high: round(base * 1.3),
    platformLabel: platform.label,
  };
}
