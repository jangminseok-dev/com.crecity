"use client";

import Link from "next/link";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { useRef, useState } from "react";
import { z } from "zod";

import MyApplications from "@/components/my-applications";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Skeleton } from "@/components/ui/skeleton";
import { Textarea } from "@/components/ui/textarea";
import { ApiError, apiFetch } from "@/lib/api";
import { useAuthStore } from "@/lib/auth-store";
import { BRIEF_SKELETON } from "@/lib/campaign-brief";
import { CREATOR_CATEGORIES, PLATFORM_LABELS, formatKrw } from "@/lib/labels";
import type { Campaign } from "@/lib/types";

const campaignSchema = z.object({
  title: z.string().min(1, "제목을 입력해 주세요.").max(100),
  description: z.string().min(10, "원하는 콘텐츠·조건을 10자 이상 적어 주세요."),
  platform: z.enum(["INSTAGRAM", "YOUTUBE", "TIKTOK", "NAVER_BLOG", "UGC"]),
  budget_krw: z.coerce.number().int().positive("예산은 0보다 커야 합니다."),
  // 선택 필드 — 빈 문자열은 미입력으로 보고 서버에 보내지 않는다
  deadline_date: z.string().optional(),
  target_category: z.string().optional(),
  target_location: z.string().optional(),
});

function CampaignManager() {
  const queryClient = useQueryClient();
  // 단일 객체 상태 — 제출 진행·오류 (입력값은 FormData 패턴)
  const [form, setForm] = useState<{ submitting: boolean; error: string | null }>({
    submitting: false,
    error: null,
  });
  // 브리프 골격을 넣을 대상 — 상태가 아니라 DOM 참조라 FormData 패턴을 깨지 않는다
  const descriptionRef = useRef<HTMLTextAreaElement>(null);

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
    const { deadline_date, target_category, target_location, ...campaign } = parsed.data;
    try {
      await apiFetch("/campaign/campaigns", {
        method: "POST",
        body: JSON.stringify({
          ...campaign,
          // 날짜만 고르므로 그날 마감(23:59:59)으로 해석한다
          deadline_at: deadline_date ? `${deadline_date}T23:59:59` : null,
          target_category: target_category || null,
          target_location: target_location || null,
        }),
      });
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
            <div className="grid gap-4 sm:grid-cols-3">
              <div className="grid gap-1.5">
                <Label htmlFor="deadline_date">지원 마감일 (선택)</Label>
                <Input id="deadline_date" name="deadline_date" type="date" />
              </div>
              <div className="grid gap-1.5">
                <Label htmlFor="target_category">타겟 카테고리 (선택)</Label>
                <select
                  id="target_category"
                  name="target_category"
                  defaultValue=""
                  className="h-9 rounded-md border border-input bg-transparent px-3 text-sm"
                >
                  <option value="">상관 없음</option>
                  {CREATOR_CATEGORIES.map((category) => (
                    <option key={category} value={category}>
                      {category}
                    </option>
                  ))}
                </select>
              </div>
              <div className="grid gap-1.5">
                <Label htmlFor="target_location">타겟 지역 (선택)</Label>
                <Input id="target_location" name="target_location" placeholder="서울" />
              </div>
            </div>
            <div className="grid gap-1.5">
              <div className="flex items-center justify-between">
                <Label htmlFor="description">상세 내용</Label>
                {/* 무엇을 적어야 할지 모르는 경우가 흔해 골격을 넣어 준다(갭 #49) */}
                <button
                  type="button"
                  onClick={() => {
                    const field = descriptionRef.current;
                    if (!field) return;
                    if (field.value.trim() && !confirm("입력한 내용을 브리프 형식으로 바꿀까요?"))
                      return;
                    field.value = BRIEF_SKELETON;
                    field.focus();
                  }}
                  className="text-[13px] font-medium text-primary hover:underline"
                >
                  브리프 형식 넣기
                </button>
              </div>
              <Textarea
                id="description"
                name="description"
                ref={descriptionRef}
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

/* 같은 URL이 계정 유형에 따라 갈린다 — 브랜드는 공고 관리, 크리에이터는 내 지원 내역(갭 #103).
   #93의 안내 화면을 크리에이터에게 실제로 쓸모 있는 화면으로 바꾼 것이다. */
export default function DashboardCampaignsPage() {
  const user = useAuthStore((s) => s.user);

  if (!user) return <Skeleton className="h-40 w-full" />;
  return user.account_type === "CREATOR" ? <MyApplications /> : <CampaignManager />;
}
