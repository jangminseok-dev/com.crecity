// 크리에이터 지표 조합 헬퍼(갭 #86·#87 공용) — 비교 화면이 공개 프로필 API를 행 단위로 읽는다.

import { ApiError, apiFetch } from "@/lib/api";
import type { CreatorProfile, ProfileAnalytics } from "@/lib/types";

export async function fetchProfile(slug: string): Promise<CreatorProfile | null> {
  try {
    return await apiFetch<CreatorProfile>(`/creator/profiles/${encodeURIComponent(slug)}`);
  } catch (error) {
    if (error instanceof ApiError && error.status === 404) return null;
    throw error;
  }
}

export function fetchAnalytics(slug: string): Promise<ProfileAnalytics[]> {
  return apiFetch<ProfileAnalytics[]>(`/creator/profiles/${encodeURIComponent(slug)}/analytics`);
}

/** 채널 중 최고 참여율(퍼밀) — vetting(#16)과 같은 관점으로 대표값을 하나만 보여준다. */
export function maxEngagementPermille(analytics: ProfileAnalytics[]): number | null {
  const values = analytics
    .map((row) => row.engagement_permille)
    .filter((value): value is number => value !== null);
  return values.length > 0 ? Math.max(...values) : null;
}
