"use client";

import { useQuery } from "@tanstack/react-query";

import { apiFetch } from "@/lib/api";
import { formatFollowers, formatKrw } from "@/lib/labels";
import { estimatePrice } from "@/lib/pricing";
import type { ProfileAnalytics } from "@/lib/types";

/**
 * 크리에이터 단가 책정 도우미(§8 약점 "가격 책정 지원 부재", 갭 #51).
 *
 * 등록해 둔 채널 지표로 참고 범위를 계산해 준다 — 지표가 없으면 아무것도 그리지 않는다
 * (근거 없는 숫자를 보여주지 않는다).
 */
export default function PackagePriceHelper({
  platform,
  onPick,
}: {
  platform: string;
  onPick: (price: number) => void;
}) {
  const { data: analytics } = useQuery({
    queryKey: ["myAnalytics"],
    queryFn: () => apiFetch<ProfileAnalytics[]>("/creator/my/analytics"),
  });

  const channel = analytics?.find((item) => item.platform === platform);
  const estimate = channel
    ? estimatePrice(platform, channel.followers_count, (channel.engagement_permille ?? 0) / 10)
    : null;

  if (!analytics) return null;

  if (!channel) {
    return (
      <p className="text-xs text-muted-foreground">
        이 플랫폼의 채널 지표를 등록하면 참고 단가를 계산해 드려요.
        {platform === "UGC" && " (UGC는 팔로워와 무관한 제작 상품이라 계산 대상이 아니에요.)"}
      </p>
    );
  }
  if (!estimate) return null;

  return (
    <div className="rounded-lg bg-muted p-3 text-xs">
      <p className="text-muted-foreground">
        팔로워 {formatFollowers(channel.followers_count)}
        {channel.engagement_permille !== null &&
          ` · 참여율 ${(channel.engagement_permille / 10).toFixed(1)}%`}{" "}
        기준 참고 단가
      </p>
      <div className="mt-1.5 flex flex-wrap items-center gap-2">
        <span className="text-sm font-semibold text-foreground">
          {formatKrw(estimate.low)} ~ {formatKrw(estimate.high)}
        </span>
        <button
          type="button"
          onClick={() => onPick(estimate.low)}
          className="rounded-full border bg-background px-2.5 py-1 font-medium transition-colors hover:border-primary"
        >
          {formatKrw(estimate.low)} 넣기
        </button>
        <button
          type="button"
          onClick={() => onPick(estimate.high)}
          className="rounded-full border bg-background px-2.5 py-1 font-medium transition-colors hover:border-primary"
        >
          {formatKrw(estimate.high)} 넣기
        </button>
      </div>
      <p className="mt-1.5 text-muted-foreground">
        시장 참고치일 뿐이며 최종 가격은 직접 정하세요.
      </p>
    </div>
  );
}
