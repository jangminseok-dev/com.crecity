"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Trash2 } from "lucide-react";
import { useState } from "react";

import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Label } from "@/components/ui/label";
import { ApiError, apiFetch } from "@/lib/api";
import { PLATFORM_LABELS, formatFollowers } from "@/lib/labels";
import type { ProfileAnalytics } from "@/lib/types";

const ANALYTICS_PLATFORMS: ProfileAnalytics["platform"][] = [
  "INSTAGRAM",
  "YOUTUBE",
  "TIKTOK",
  "NAVER_BLOG",
];

/** 대시보드 채널 지표 관리 — 자가입력 + 스크린샷 인증(§9.2), 플랫폼당 1건(재제출=갱신). */
/* 오디언스 구간(§2.1-6) — 백엔드 `audience_breakdown.py`의 고정 목록과 1:1 */
const AUDIENCE_FIELDS = [
  { dimension: "AGE", bucket: "10s", field: "age_10s", label: "10대" },
  { dimension: "AGE", bucket: "20s", field: "age_20s", label: "20대" },
  { dimension: "AGE", bucket: "30s", field: "age_30s", label: "30대" },
  { dimension: "AGE", bucket: "40s", field: "age_40s", label: "40대" },
  { dimension: "AGE", bucket: "50s+", field: "age_50s", label: "50대+" },
  { dimension: "GENDER", bucket: "FEMALE", field: "gender_female", label: "여성" },
  { dimension: "GENDER", bucket: "MALE", field: "gender_male", label: "남성" },
  { dimension: "GENDER", bucket: "OTHER", field: "gender_other", label: "기타" },
] as const;

export default function AnalyticsManager() {
  const queryClient = useQueryClient();
  // 단일 객체 상태 — 오류 메시지 (입력값은 FormData 패턴)
  const [ui, setUi] = useState<{ error: string | null }>({ error: null });

  const { data: analytics } = useQuery({
    queryKey: ["myAnalytics"],
    queryFn: () => apiFetch<ProfileAnalytics[]>("/creator/my/analytics"),
  });

  const invalidate = () => queryClient.invalidateQueries({ queryKey: ["myAnalytics"] });

  const submit = useMutation({
    mutationFn: (form: FormData) =>
      apiFetch<ProfileAnalytics>("/creator/my/analytics", { method: "POST", body: form }),
    onSuccess: () => {
      setUi({ error: null });
      void invalidate();
    },
    onError: (error) =>
      setUi({ error: error instanceof ApiError ? error.detail : "등록에 실패했습니다." }),
  });

  const remove = useMutation({
    mutationFn: (platform: string) =>
      apiFetch<void>(`/creator/my/analytics/${platform}`, { method: "DELETE" }),
    onSuccess: invalidate,
  });

  const handleSubmit = (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    const formElement = e.currentTarget;
    const raw = new FormData(formElement);
    const engagementPercent = String(raw.get("engagement_percent") ?? "").trim();
    const form = new FormData();
    form.append("platform", String(raw.get("platform")));
    form.append("followers_count", String(raw.get("followers_count")));
    // 백엔드는 정수 ‰(퍼밀) — 3.5% 입력 → 35
    if (engagementPercent) {
      form.append("engagement_permille", String(Math.round(Number(engagementPercent) * 10)));
    }
    // 오디언스(갭 #67) — 입력한 구간만 보낸다. 비율은 %로 받아 ‰로 바꾼다
    const shares = AUDIENCE_FIELDS.flatMap(({ dimension, bucket, field }) => {
      const percent = String(raw.get(field) ?? "").trim();
      if (!percent) return [];
      return [{ dimension, bucket, share_permille: Math.round(Number(percent) * 10) }];
    });
    if (shares.length > 0) form.append("audience", JSON.stringify(shares));
    const region = String(raw.get("top_audience_region") ?? "").trim();
    if (region) form.append("top_audience_region", region);

    const file = raw.get("file");
    if (!(file instanceof File) || file.size === 0) {
      setUi({ error: "인증 스크린샷을 첨부해 주세요." });
      return;
    }
    form.append("file", file);
    submit.mutate(form, { onSuccess: () => formElement.reset() });
  };

  return (
    <Card>
      <CardContent className="p-6">
        <p className="font-semibold">채널 분석 지표</p>
        <p className="mt-1 text-sm text-muted-foreground">
          팔로워 수·참여율을 입력하면 프로필에 표시됩니다. 관리 화면 스크린샷이 인증 증빙이
          되며, 같은 플랫폼에 다시 제출하면 갱신됩니다.
        </p>

        {analytics && analytics.length > 0 && (
          <div className="mt-4 grid gap-2">
            {analytics.map((row) => (
              <div key={row.platform} className="flex items-center gap-3 rounded-lg border px-3 py-2.5 text-sm">
                <span className="w-28 shrink-0 font-medium">{PLATFORM_LABELS[row.platform]}</span>
                <span className="flex-1 text-muted-foreground">
                  팔로워 {formatFollowers(row.followers_count)}
                  {row.engagement_permille !== null &&
                    ` · 참여율 ${(row.engagement_permille / 10).toFixed(1)}%`}
                </span>
                <button
                  type="button"
                  aria-label="지표 삭제"
                  onClick={() => remove.mutate(row.platform)}
                  className="inline-flex size-8 shrink-0 items-center justify-center rounded-full text-muted-foreground transition-colors hover:bg-secondary hover:text-destructive"
                >
                  <Trash2 className="size-4" />
                </button>
              </div>
            ))}
          </div>
        )}

        <form onSubmit={handleSubmit} className="mt-5 grid gap-3.5">
          <div className="grid grid-cols-2 gap-3">
            <div className="grid gap-1.5">
              <Label htmlFor="analytics-platform">플랫폼</Label>
              <select
                id="analytics-platform"
                name="platform"
                className="h-10 rounded-lg border border-input bg-transparent px-3 text-sm"
              >
                {ANALYTICS_PLATFORMS.map((platform) => (
                  <option key={platform} value={platform}>
                    {PLATFORM_LABELS[platform]}
                  </option>
                ))}
              </select>
            </div>
            <div className="grid gap-1.5">
              <Label htmlFor="analytics-followers">팔로워 수</Label>
              <input
                id="analytics-followers"
                name="followers_count"
                type="number"
                min={1}
                required
                placeholder="예: 25000"
                className="h-10 rounded-lg border border-input bg-transparent px-3 text-sm outline-none focus:border-primary"
              />
            </div>
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div className="grid gap-1.5">
              <Label htmlFor="analytics-engagement">참여율 % (선택)</Label>
              <input
                id="analytics-engagement"
                name="engagement_percent"
                type="number"
                min={0}
                max={100}
                step={0.1}
                placeholder="예: 3.5"
                className="h-10 rounded-lg border border-input bg-transparent px-3 text-sm outline-none focus:border-primary"
              />
            </div>
            <div className="grid gap-1.5">
              <Label htmlFor="analytics-file">인증 스크린샷</Label>
              <input
                id="analytics-file"
                name="file"
                type="file"
                accept="image/jpeg,image/png,image/webp"
                required
                className="h-10 rounded-lg border border-input bg-transparent px-2 py-1.5 text-sm file:mr-2 file:rounded-md file:border-0 file:bg-secondary file:px-2.5 file:py-1 file:text-xs"
              />
            </div>
          </div>
          {/* 오디언스(§2.1-6, 갭 #67) — 전부 채울 필요 없이 아는 구간만 */}
          <details className="rounded-lg border p-3">
            <summary className="cursor-pointer text-sm font-medium">
              오디언스 정보 (선택) — 브랜드가 타겟 적합성을 판단합니다
            </summary>
            <div className="mt-3 grid gap-3">
              <div className="grid gap-1.5">
                <Label htmlFor="analytics-region">주 오디언스 지역</Label>
                <input
                  id="analytics-region"
                  name="top_audience_region"
                  maxLength={50}
                  placeholder="예: 서울"
                  className="h-10 rounded-lg border border-input bg-transparent px-3 text-sm outline-none focus:border-primary"
                />
              </div>
              <p className="text-xs text-muted-foreground">
                아는 구간만 % 로 적으세요. 같은 항목(연령·성별)의 합이 100%를 넘으면 등록되지
                않습니다.
              </p>
              <div className="grid grid-cols-3 gap-2 sm:grid-cols-4">
                {AUDIENCE_FIELDS.map((item) => (
                  <div key={item.field} className="grid gap-1">
                    <Label htmlFor={`analytics-${item.field}`} className="text-xs">
                      {item.label}
                    </Label>
                    <input
                      id={`analytics-${item.field}`}
                      name={item.field}
                      type="number"
                      min={0}
                      max={100}
                      step={0.1}
                      placeholder="%"
                      className="h-9 rounded-lg border border-input bg-transparent px-2 text-sm outline-none focus:border-primary"
                    />
                  </div>
                ))}
              </div>
            </div>
          </details>
          {ui.error && <p className="text-sm text-destructive">{ui.error}</p>}
          <Button type="submit" disabled={submit.isPending} className="justify-self-start">
            {submit.isPending ? "등록 중…" : "지표 등록·갱신"}
          </Button>
        </form>
      </CardContent>
    </Card>
  );
}
