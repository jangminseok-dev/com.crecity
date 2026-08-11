"use client";

import Link from "next/link";
import { useState } from "react";

import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Label } from "@/components/ui/label";
import { formatKrw } from "@/lib/labels";

/* 플랫폼별 팔로워 1명당 기본 단가(원) — 국내 시장 통상 범위의 중간값 참고치 */
const PLATFORM_RATES: { value: string; label: string; perFollower: number }[] = [
  { value: "INSTAGRAM", label: "인스타그램 (릴스·피드)", perFollower: 15 },
  { value: "YOUTUBE", label: "유튜브 (영상 1편)", perFollower: 40 },
  { value: "TIKTOK", label: "틱톡 (영상 1편)", perFollower: 12 },
  { value: "NAVER_BLOG", label: "네이버 블로그 (포스팅 1건)", perFollower: 10 },
];

/* 참여율 구간별 보정 — 참여가 높을수록 단가가 올라간다 */
function engagementMultiplier(engagementRate: number): number {
  if (engagementRate <= 0) return 1;
  if (engagementRate < 1) return 0.7;
  if (engagementRate < 3) return 1;
  if (engagementRate < 6) return 1.3;
  return 1.6;
}

type Estimate = { low: number; high: number; platformLabel: string };

export default function PricingCalculator() {
  // 단일 객체 상태 — 계산 결과 (입력값은 FormData 패턴)
  const [estimate, setEstimate] = useState<Estimate | null>(null);

  const handleSubmit = (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    const form = new FormData(e.currentTarget);
    const platform = PLATFORM_RATES.find((p) => p.value === form.get("platform"));
    const followers = Number(form.get("followers"));
    const engagement = Number(form.get("engagement")) || 0;
    if (!platform || !followers || followers <= 0) return;

    const base = followers * platform.perFollower * engagementMultiplier(engagement);
    // 협상 폭 ±30% — 만 원 단위 반올림
    const round = (value: number) => Math.max(10000, Math.round(value / 10000) * 10000);
    setEstimate({
      low: round(base * 0.7),
      high: round(base * 1.3),
      platformLabel: platform.label,
    });
  };

  return (
    <div className="grid gap-5">
      <Card>
        <CardContent className="p-6">
          <form onSubmit={handleSubmit} className="grid gap-4">
            <div className="grid gap-1.5">
              <Label htmlFor="platform">플랫폼</Label>
              <select
                id="platform"
                name="platform"
                defaultValue="INSTAGRAM"
                className="h-10 rounded-lg border border-input bg-transparent px-3 text-sm"
              >
                {PLATFORM_RATES.map((p) => (
                  <option key={p.value} value={p.value}>
                    {p.label}
                  </option>
                ))}
              </select>
            </div>
            <div className="grid gap-1.5">
              <Label htmlFor="followers">팔로워(구독자) 수</Label>
              <input
                id="followers"
                name="followers"
                type="number"
                min={100}
                required
                placeholder="예: 25000"
                className="h-10 rounded-lg border border-input bg-transparent px-3 text-sm outline-none focus:border-primary"
              />
            </div>
            <div className="grid gap-1.5">
              <Label htmlFor="engagement">평균 참여율 % (선택)</Label>
              <input
                id="engagement"
                name="engagement"
                type="number"
                min={0}
                max={100}
                step={0.1}
                placeholder="모르면 비워 두세요 — 참여율 계산기로 확인할 수 있어요"
                className="h-10 rounded-lg border border-input bg-transparent px-3 text-sm outline-none focus:border-primary"
              />
            </div>
            <Button type="submit" className="justify-self-start">
              단가 계산하기
            </Button>
          </form>
        </CardContent>
      </Card>

      {estimate && (
        <Card>
          <CardContent className="p-6 text-center">
            <p className="text-sm text-muted-foreground">{estimate.platformLabel} 예상 단가 범위</p>
            <p className="mt-2 text-[28px] font-extrabold tracking-[-0.02em]">
              {formatKrw(estimate.low)} ~ {formatKrw(estimate.high)}
            </p>
            <p className="mt-2 text-[13px] text-muted-foreground">
              콘텐츠 1건 기준 시장 참고치입니다 — 실제 단가는 콘텐츠 형식·2차 활용 범위에 따라
              달라집니다.
            </p>
            <Button
              className="mt-5"
              nativeButton={false}
              render={<Link href="/">가격이 공개된 크리에이터 보러 가기</Link>}
            />
          </CardContent>
        </Card>
      )}
    </div>
  );
}
