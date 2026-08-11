"use client";

import Link from "next/link";
import { useState } from "react";

import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Label } from "@/components/ui/label";

/* 통상 벤치마크(마이크로 인플루언서 기준) — 결과 해석용 */
const GRADES: { min: number; label: string; tone: string; desc: string }[] = [
  { min: 6, label: "매우 좋음", tone: "text-[#16a34a]", desc: "상위권 참여율 — 팔로워와의 신뢰가 높은 계정입니다." },
  { min: 3, label: "좋음", tone: "text-[#16a34a]", desc: "평균 이상 — 협업 성과를 기대할 수 있는 참여율입니다." },
  { min: 1, label: "보통", tone: "text-[#ca8a04]", desc: "통상 범위 — 콘텐츠 품질과 함께 종합적으로 판단하세요." },
  { min: 0, label: "낮음", tone: "text-[#e5484d]", desc: "팔로워 대비 반응이 적은 편 — 가짜 팔로워 여부도 확인해 보세요." },
];

type Result = { rate: number; grade: (typeof GRADES)[number] };

export default function EngagementCalculator() {
  // 단일 객체 상태 — 계산 결과 (입력값은 FormData 패턴)
  const [result, setResult] = useState<Result | null>(null);

  const handleSubmit = (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    const form = new FormData(e.currentTarget);
    const followers = Number(form.get("followers"));
    const likes = Number(form.get("likes")) || 0;
    const comments = Number(form.get("comments")) || 0;
    if (!followers || followers <= 0) return;

    // 참여율 = (평균 좋아요 + 평균 댓글) ÷ 팔로워 × 100 — 통용 공식
    const rate = ((likes + comments) / followers) * 100;
    const grade = GRADES.find((g) => rate >= g.min) ?? GRADES[GRADES.length - 1];
    setResult({ rate, grade });
  };

  return (
    <div className="grid gap-5">
      <Card>
        <CardContent className="p-6">
          <form onSubmit={handleSubmit} className="grid gap-4">
            <div className="grid gap-1.5">
              <Label htmlFor="followers">팔로워 수</Label>
              <input
                id="followers"
                name="followers"
                type="number"
                min={1}
                required
                placeholder="예: 25000"
                className="h-10 rounded-lg border border-input bg-transparent px-3 text-sm outline-none focus:border-primary"
              />
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div className="grid gap-1.5">
                <Label htmlFor="likes">게시물 평균 좋아요</Label>
                <input
                  id="likes"
                  name="likes"
                  type="number"
                  min={0}
                  required
                  placeholder="예: 900"
                  className="h-10 rounded-lg border border-input bg-transparent px-3 text-sm outline-none focus:border-primary"
                />
              </div>
              <div className="grid gap-1.5">
                <Label htmlFor="comments">게시물 평균 댓글</Label>
                <input
                  id="comments"
                  name="comments"
                  type="number"
                  min={0}
                  placeholder="예: 40"
                  className="h-10 rounded-lg border border-input bg-transparent px-3 text-sm outline-none focus:border-primary"
                />
              </div>
            </div>
            <p className="text-[13px] text-muted-foreground">
              최근 게시물 10~12개의 평균값을 넣으면 정확합니다.
            </p>
            <Button type="submit" className="justify-self-start">
              참여율 계산하기
            </Button>
          </form>
        </CardContent>
      </Card>

      {result && (
        <Card>
          <CardContent className="p-6 text-center">
            <p className="text-sm text-muted-foreground">참여율 (Engagement Rate)</p>
            <p className="mt-2 text-[34px] font-extrabold tracking-[-0.02em]">
              {result.rate.toFixed(2)}%
              <span className={`ml-2 text-lg font-bold ${result.grade.tone}`}>
                {result.grade.label}
              </span>
            </p>
            <p className="mt-2 text-[13px] text-muted-foreground">{result.grade.desc}</p>
            <Button
              className="mt-5"
              nativeButton={false}
              render={<Link href="/tools/pricing-calculator">이 참여율로 광고 단가 계산하기</Link>}
            />
          </CardContent>
        </Card>
      )}
    </div>
  );
}
