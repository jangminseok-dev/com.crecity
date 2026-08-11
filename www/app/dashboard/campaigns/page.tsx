"use client";

import Link from "next/link";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { z } from "zod";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Skeleton } from "@/components/ui/skeleton";
import { Textarea } from "@/components/ui/textarea";
import { ApiError, apiFetch } from "@/lib/api";
import { PLATFORM_LABELS, formatKrw } from "@/lib/labels";
import type { Campaign } from "@/lib/types";

const campaignSchema = z.object({
  title: z.string().min(1, "제목을 입력해 주세요.").max(100),
  description: z.string().min(10, "원하는 콘텐츠·조건을 10자 이상 적어 주세요."),
  platform: z.enum(["INSTAGRAM", "YOUTUBE", "TIKTOK", "NAVER_BLOG", "UGC"]),
  budget_krw: z.coerce.number().int().positive("예산은 0보다 커야 합니다."),
});

export default function DashboardCampaignsPage() {
  const queryClient = useQueryClient();
  // 단일 객체 상태 — 제출 진행·오류 (입력값은 FormData 패턴)
  const [form, setForm] = useState<{ submitting: boolean; error: string | null }>({
    submitting: false,
    error: null,
  });

  const { data: campaigns, isPending } = useQuery({
    queryKey: ["myCampaigns"],
    queryFn: () => apiFetch<Campaign[]>("/campaign/my/campaigns"),
  });

  const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    const formElement = e.currentTarget;
    const parsed = campaignSchema.safeParse(Object.fromEntries(new FormData(formElement).entries()));
    if (!parsed.success) {
      setForm({ submitting: false, error: parsed.error.issues[0].message });
      return;
    }
    setForm({ submitting: true, error: null });
    try {
      await apiFetch("/campaign/campaigns", { method: "POST", body: JSON.stringify(parsed.data) });
      formElement.reset();
      setForm({ submitting: false, error: null });
      await queryClient.invalidateQueries({ queryKey: ["myCampaigns"] });
    } catch (error) {
      setForm({
        submitting: false,
        error: error instanceof ApiError ? error.detail : "공고 등록에 실패했습니다.",
      });
    }
  };

  return (
    <div className="grid gap-6">
      <Card>
        <CardContent className="p-6">
          <h3 className="font-semibold">새 공고 올리기</h3>
          <p className="mt-1 text-sm text-muted-foreground">
            원하는 콘텐츠를 공고로 올리면 크리에이터들이 견적으로 지원합니다.
          </p>
          <form onSubmit={handleSubmit} className="mt-4 grid gap-4">
            <div className="grid gap-1.5">
              <Label htmlFor="title">제목</Label>
              <Input id="title" name="title" placeholder="신제품 클렌저 리뷰 릴스 제작" />
            </div>
            <div className="grid gap-4 sm:grid-cols-2">
              <div className="grid gap-1.5">
                <Label htmlFor="platform">플랫폼</Label>
                <select
                  id="platform"
                  name="platform"
                  defaultValue="INSTAGRAM"
                  className="h-9 rounded-md border border-input bg-transparent px-3 text-sm"
                >
                  {Object.entries(PLATFORM_LABELS).map(([value, label]) => (
                    <option key={value} value={value}>{label}</option>
                  ))}
                </select>
              </div>
              <div className="grid gap-1.5">
                <Label htmlFor="budget_krw">예산 (원)</Label>
                <Input id="budget_krw" name="budget_krw" type="number" min={1} placeholder="500000" />
              </div>
            </div>
            <div className="grid gap-1.5">
              <Label htmlFor="description">상세 내용</Label>
              <Textarea
                id="description"
                name="description"
                rows={4}
                placeholder="원하는 콘텐츠 방향·필수 조건·일정 등을 적어 주세요."
              />
            </div>
            {form.error && <p className="text-sm text-destructive">{form.error}</p>}
            <Button type="submit" disabled={form.submitting} className="justify-self-start">
              {form.submitting ? "등록 중…" : "공고 등록"}
            </Button>
          </form>
        </CardContent>
      </Card>

      <div>
        <h3 className="mb-3 font-semibold">내 공고 {campaigns && `(${campaigns.length})`}</h3>
        {isPending ? (
          <Skeleton className="h-32 w-full" />
        ) : !campaigns || campaigns.length === 0 ? (
          <p className="rounded-xl border border-dashed py-10 text-center text-sm text-muted-foreground">
            아직 올린 공고가 없습니다.
          </p>
        ) : (
          <div className="grid gap-3">
            {campaigns.map((campaign) => (
              <Link key={campaign.id} href={`/campaigns/${campaign.id}`}>
                <Card className="transition-shadow hover:shadow-md">
                  <CardContent className="flex items-center justify-between gap-4 p-4">
                    <div className="flex min-w-0 items-center gap-2">
                      <Badge variant={campaign.status === "OPEN" ? "secondary" : "destructive"}>
                        {campaign.status === "OPEN" ? "접수 중" : "마감"}
                      </Badge>
                      <p className="truncate font-medium">{campaign.title}</p>
                    </div>
                    <p className="shrink-0 text-sm font-semibold">
                      {formatKrw(campaign.budget_krw)}
                    </p>
                  </CardContent>
                </Card>
              </Link>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
