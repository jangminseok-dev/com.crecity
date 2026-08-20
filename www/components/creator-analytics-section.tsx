"use client";

import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import { BarChart3, BadgeCheck } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { apiFetch } from "@/lib/api";
import { useAuthStore } from "@/lib/auth-store";
import { PLATFORM_LABELS, formatFollowers } from "@/lib/labels";
import type { ProfileAnalytics } from "@/lib/types";

/* 백엔드 audience_breakdown.py의 고정 구간 — 표시용 라벨 */
const AUDIENCE_ORDER = ["AGE", "GENDER"] as const;
const AUDIENCE_LABELS: Record<string, string> = {
  "10s": "10대",
  "20s": "20대",
  "30s": "30대",
  "40s": "40대",
  "50s+": "50대+",
  FEMALE: "여성",
  MALE: "남성",
  OTHER: "기타",
};

/** 프로필 Analytics 섹션 — 비로그인은 가입 게이트(§9.2), 로그인 시 채널별 지표 표. */
export default function CreatorAnalyticsSection({ slug }: { slug: string }) {
  const status = useAuthStore((s) => s.status);

  const { data: analytics } = useQuery({
    queryKey: ["profileAnalytics", slug],
    queryFn: () =>
      apiFetch<ProfileAnalytics[]>(`/creator/profiles/${encodeURIComponent(slug)}/analytics`),
    enabled: status === "authenticated",
  });

  if (status === "loading") return null;

  // 가입 게이트 — 지표는 회원에게만 연다(리드 캡처)
  if (status === "guest") {
    return (
      <Card>
        <CardContent className="flex flex-col items-center gap-3 p-8 text-center">
          <BarChart3 className="size-7 text-muted-foreground" />
          <p className="font-semibold">팔로워·참여율은 회원에게만 공개돼요</p>
          <p className="text-sm text-muted-foreground">
            무료로 가입하면 이 크리에이터의 채널별 팔로워 수와 참여율을 확인할 수 있습니다.
          </p>
          <Button className="mt-1" nativeButton={false} render={<Link href="/login">무료로 가입하고 보기</Link>} />
        </CardContent>
      </Card>
    );
  }

  if (!analytics || analytics.length === 0) {
    return (
      <p className="rounded-xl border border-dashed py-8 text-center text-sm text-muted-foreground">
        아직 등록된 채널 분석 정보가 없습니다.
      </p>
    );
  }

  return (
    <div className="grid gap-2.5">
      {analytics.map((row) => (
        <div key={row.platform} className="rounded-xl border px-4 py-3.5">
          <div className="flex items-center gap-4">
          <p className="w-32 shrink-0 text-sm font-semibold">{PLATFORM_LABELS[row.platform]}</p>
          <div className="flex flex-1 flex-wrap items-baseline gap-x-6 gap-y-1">
            <p className="text-sm">
              <span className="text-muted-foreground">팔로워 </span>
              <span className="font-bold">{formatFollowers(row.followers_count)}</span>
            </p>
            {row.engagement_permille !== null && (
              <p className="text-sm">
                <span className="text-muted-foreground">참여율 </span>
                <span className="font-bold">{(row.engagement_permille / 10).toFixed(1)}%</span>
              </p>
            )}
            {row.avg_views !== null && (
              <p className="text-sm">
                <span className="text-muted-foreground">평균 조회수 </span>
                <span className="font-bold">{formatFollowers(row.avg_views)}</span>
              </p>
            )}
          </div>
          <a
            href={`/api/backend${row.screenshot_url}`}
            target="_blank"
            rel="noreferrer"
            className="inline-flex shrink-0 items-center gap-1 text-[13px] text-muted-foreground underline-offset-2 hover:underline"
            title="자가입력 지표의 증빙 스크린샷"
          >
            <BadgeCheck className="size-4 text-primary" />
            스크린샷 인증
          </a>
          </div>
          {/* 오디언스(§2.1-6, 갭 #67) — 입력한 구간만 보여준다 */}
          {(row.top_audience_region || row.audience.length > 0) && (
            <div className="mt-3 flex flex-wrap items-center gap-x-4 gap-y-1.5 border-t pt-3 text-[13px]">
              <span className="text-muted-foreground">오디언스</span>
              {row.top_audience_region && (
                <span>
                  주 지역 <span className="font-semibold">{row.top_audience_region}</span>
                </span>
              )}
              {AUDIENCE_ORDER.map((dimension) => {
                const shares = row.audience
                  .filter((item) => item.dimension === dimension)
                  .sort((a, b) => b.share_permille - a.share_permille);
                if (shares.length === 0) return null;
                return (
                  <span key={dimension}>
                    {shares
                      .map(
                        (item) =>
                          `${AUDIENCE_LABELS[item.bucket] ?? item.bucket} ${(item.share_permille / 10).toFixed(0)}%`,
                      )
                      .join(" · ")}
                  </span>
                );
              })}
            </div>
          )}
        </div>
      ))}
      <p className="text-xs text-muted-foreground">
        크리에이터가 직접 입력하고 스크린샷으로 인증한 수치입니다.
      </p>
    </div>
  );
}
