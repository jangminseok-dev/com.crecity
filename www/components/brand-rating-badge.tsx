"use client";

import { useQuery } from "@tanstack/react-query";

import { apiFetch } from "@/lib/api";

type BrandRating = {
  average_score: number | null;
  total: number;
};

/**
 * 브랜드 평점 집계(갭 #83, 공개 API) — 크리에이터가 수락을 판단할 때 참고한다.
 * 평가가 0건이면 아무것도 그리지 않는다 — "평점 없음"은 신규 브랜드를 부당하게
 * 나빠 보이게 한다(#65 거래 이력과 같은 원칙).
 */
export default function BrandRatingBadge({ brandUserId }: { brandUserId: number }) {
  const { data } = useQuery({
    queryKey: ["brandRating", brandUserId],
    queryFn: () => apiFetch<BrandRating>(`/review/brands/${brandUserId}/rating`),
  });

  if (!data || data.total === 0 || data.average_score === null) return null;

  return (
    <p className="mt-1 text-xs text-muted-foreground">
      크리에이터 평가 ⭐ {data.average_score} ({data.total}건)
    </p>
  );
}
