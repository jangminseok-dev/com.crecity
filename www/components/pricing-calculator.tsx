"use client";

import Link from "next/link";
import { useState } from "react";

import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Label } from "@/components/ui/label";
import { formatKrw } from "@/lib/labels";
import { PLATFORM_RATES, estimatePrice, type Estimate } from "@/lib/pricing";


export default function PricingCalculator() {
  // 단일 객체 상태 — 계산 결과 (입력값은 FormData 패턴)
  const [estimate, setEstimate] = useState<Estimate | null>(null);

  const handleSubmit = (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    const form = new FormData(e.currentTarget);
    const result = estimatePrice(
      String(form.get("platform") ?? ""),
      Number(form.get("followers")),
      Number(form.get("engagement")) || 0
    );
    if (result) setEstimate(result);
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
