"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import Link from "next/link";
import { useState } from "react";

import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { ApiError, apiFetch } from "@/lib/api";
import { PLATFORM_LABELS, formatFollowers } from "@/lib/labels";

type FlaggedAnalytics = {
  id: number;
  profile_slug: string;
  profile_name: string;
  platform: string;
  followers_count: number;
  engagement_permille: number | null;
  flag_reason: string;
  updated_at: string | null;
};

/** 이상치 지표 재검토 큐(갭 #82) — profile.review 권한. 확인 처리 또는 프로필 반려로 대응한다. */
export default function AdminFlaggedAnalytics() {
  const queryClient = useQueryClient();
  // 단일 값 상태 — 처리 실패 메시지
  const [error, setError] = useState<string | null>(null);

  const { data: flagged } = useQuery({
    queryKey: ["flaggedAnalytics"],
    queryFn: () => apiFetch<FlaggedAnalytics[]>("/admin/analytics/flagged"),
  });

  const clear = useMutation({
    mutationFn: (id: number) =>
      apiFetch(`/admin/analytics/${id}/clear-flag`, { method: "POST" }),
    onSuccess: async () => {
      setError(null);
      await queryClient.invalidateQueries({ queryKey: ["flaggedAnalytics"] });
    },
    onError: (mutationError) =>
      setError(mutationError instanceof ApiError ? mutationError.detail : "처리에 실패했습니다."),
  });

  return (
    <section className="mt-12">
      <h2 className="text-xl font-bold tracking-[-0.02em]">지표 재검토</h2>
      <p className="mt-1 text-sm text-muted-foreground">
        자가 입력 지표에서 이상치가 감지되면 여기에 쌓입니다 — 스크린샷과 대조해 확인 처리하거나,
        문제가 있으면 프로필을 반려하세요.
      </p>
      {error && <p className="mt-3 text-sm text-destructive">{error}</p>}
      <div className="mt-4 grid gap-3">
        {!flagged || flagged.length === 0 ? (
          <p className="rounded-xl border border-dashed py-12 text-center text-sm text-muted-foreground">
            재검토할 지표가 없습니다.
          </p>
        ) : (
        flagged.map((item) => (
          <Card key={item.id}>
            <CardContent className="flex flex-wrap items-center justify-between gap-3 p-5">
              <div>
                <p className="font-semibold">
                  <Link href={`/creators/${item.profile_slug}`} className="hover:underline">
                    {item.profile_name}
                  </Link>{" "}
                  · {PLATFORM_LABELS[item.platform as keyof typeof PLATFORM_LABELS] ?? item.platform}
                </p>
                <p className="mt-1 text-sm text-destructive">⚠️ {item.flag_reason}</p>
                <p className="mt-1 text-xs text-muted-foreground">
                  팔로워 {formatFollowers(item.followers_count)}
                  {item.engagement_permille !== null &&
                    ` · 참여율 ${(item.engagement_permille / 10).toFixed(1)}%`}
                </p>
              </div>
              <Button
                variant="outline"
                size="sm"
                disabled={clear.isPending}
                onClick={() => clear.mutate(item.id)}
              >
                확인 처리
              </Button>
            </CardContent>
          </Card>
        ))
        )}
      </div>
    </section>
  );
}
