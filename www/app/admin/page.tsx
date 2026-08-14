"use client";

import Link from "next/link";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";

import AdminAnnualPayouts from "@/components/admin-annual-payouts";
import AdminAuditLogs from "@/components/admin-audit-logs";
import AdminDashboardMetrics from "@/components/admin-dashboard-metrics";
import AdminDisputes from "@/components/admin-disputes";
import AdminOrderSearch from "@/components/admin-order-search";
import AdminReports from "@/components/admin-reports";
import AdminWithdrawals from "@/components/admin-withdrawals";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { ApiError, apiFetch } from "@/lib/api";
import { useAuthStore } from "@/lib/auth-store";

type PendingProfile = {
  id: number;
  slug: string;
  name: string;
  tagline: string;
  bio: string;
  primary_category: string;
  status: string;
  created_at: string | null;
  platform_count: number;
  total_followers: number;
  best_engagement_permille: number | null;
  min_followers: number;
  min_engagement_permille: number;
  vetting_passed: boolean;
};

/** 정량 기준 자동 체크 — 자가입력 지표라 참고선일 뿐, 최종 판단은 스크린샷을 보고 한다. */
function VettingChecklist({ profile }: { profile: PendingProfile }) {
  const followersOk = profile.total_followers >= profile.min_followers;
  const engagementOk =
    profile.best_engagement_permille !== null &&
    profile.best_engagement_permille >= profile.min_engagement_permille;
  const rows = [
    {
      ok: profile.platform_count > 0,
      label: `채널 지표 등록 ${profile.platform_count}개`,
    },
    {
      ok: followersOk,
      label: `팔로워 합계 ${profile.total_followers.toLocaleString("ko-KR")}명 (기준 ${profile.min_followers.toLocaleString("ko-KR")}명)`,
    },
    {
      ok: engagementOk,
      label: `참여율 ${
        profile.best_engagement_permille === null
          ? "미입력"
          : `${(profile.best_engagement_permille / 10).toFixed(1)}%`
      } (기준 ${(profile.min_engagement_permille / 10).toFixed(1)}%)`,
    },
  ];

  return (
    <div className="rounded-md bg-muted p-3">
      <p className="text-xs font-semibold">
        정량 기준 {profile.vetting_passed ? "충족" : "미충족"} — 참고용(자가입력 지표)
      </p>
      <ul className="mt-2 grid gap-1 text-[13px]">
        {rows.map((row) => (
          <li key={row.label} className={row.ok ? "text-muted-foreground" : "text-destructive"}>
            {row.ok ? "✓" : "✕"} {row.label}
          </li>
        ))}
      </ul>
    </div>
  );
}

export default function AdminPage() {
  const { status, user } = useAuthStore();
  const queryClient = useQueryClient();
  // 단일 값 상태 — 심사 실패 메시지
  const [reviewError, setReviewError] = useState<string | null>(null);

  const canReview = user?.permissions.includes("profile.review") ?? false;
  const { data: profiles, isPending } = useQuery({
    queryKey: ["pendingProfiles"],
    queryFn: () => apiFetch<PendingProfile[]>("/admin/profiles/pending"),
    enabled: canReview,
  });

  const review = useMutation({
    mutationFn: ({ profileId, approve }: { profileId: number; approve: boolean }) =>
      apiFetch(`/admin/profiles/${profileId}/${approve ? "approve" : "reject"}`, {
        method: "POST",
      }),
    onSuccess: async () => {
      setReviewError(null);
      await queryClient.invalidateQueries({ queryKey: ["pendingProfiles"] });
    },
    onError: (error) =>
      setReviewError(error instanceof ApiError ? error.detail : "심사 처리에 실패했습니다."),
  });

  if (status === "loading") {
    return (
      <div className="mx-auto max-w-3xl px-4 py-10">
        <Skeleton className="h-64 w-full" />
      </div>
    );
  }
  if (!canReview) {
    return (
      <p className="mx-auto max-w-3xl px-4 py-20 text-center text-muted-foreground">
        운영자 권한(profile.review)이 있는 계정만 접근할 수 있습니다.
      </p>
    );
  }

  return (
    <div className="mx-auto max-w-3xl px-4 py-10">
      <h1 className="mb-8 text-2xl font-bold tracking-[-0.02em]">운영 콘솔</h1>

      {(user?.permissions.includes("dashboard.view") ?? false) && <AdminDashboardMetrics />}

      <h2 className="text-xl font-bold tracking-[-0.02em]">프로필 심사</h2>
      <p className="mt-1 text-sm text-muted-foreground">
        승인하면 즉시 마켓플레이스 목록에 노출됩니다. 반려해도 프로필 링크 직접 공유는
        가능합니다(목록 제외만).
      </p>

      {reviewError && <p className="mt-4 text-sm text-destructive">{reviewError}</p>}

      <div className="mt-6 grid gap-4">
        {isPending ? (
          <Skeleton className="h-40 w-full" />
        ) : !profiles || profiles.length === 0 ? (
          <p className="rounded-xl border border-dashed py-16 text-center text-muted-foreground">
            심사 대기 중인 프로필이 없습니다.
          </p>
        ) : (
          profiles.map((profile) => (
            <Card key={profile.id}>
              <CardContent className="grid gap-3 p-5">
                <div className="flex items-center gap-2">
                  <p className="font-semibold">{profile.name}</p>
                  <Badge variant="secondary">{profile.primary_category}</Badge>
                  <Link
                    href={`/creators/${profile.slug}`}
                    target="_blank"
                    className="text-sm text-muted-foreground underline underline-offset-2"
                  >
                    공개 페이지 미리 보기 ↗
                  </Link>
                </div>
                <p className="text-sm text-muted-foreground">{profile.tagline}</p>
                <p className="line-clamp-3 whitespace-pre-line text-sm">{profile.bio}</p>
                <VettingChecklist profile={profile} />
                <div className="flex gap-2">
                  <Button
                    size="sm"
                    disabled={review.isPending}
                    onClick={() => review.mutate({ profileId: profile.id, approve: true })}
                  >
                    승인
                  </Button>
                  <Button
                    size="sm"
                    variant="destructive"
                    disabled={review.isPending}
                    onClick={() => {
                      if (window.confirm(`"${profile.name}" 프로필을 반려할까요?`)) {
                        review.mutate({ profileId: profile.id, approve: false });
                      }
                    }}
                  >
                    반려
                  </Button>
                </div>
              </CardContent>
            </Card>
          ))
        )}
      </div>

      {(user?.permissions.includes("withdrawal.settle") ?? false) && (
        <>
          <AdminWithdrawals />
          <AdminAnnualPayouts />
        </>
      )}
      {(user?.permissions.includes("dispute.resolve") ?? false) && <AdminDisputes />}
      {(user?.permissions.includes("report.review") ?? false) && <AdminReports />}
      {(user?.permissions.includes("order.search") ?? false) && <AdminOrderSearch />}
      <AdminAuditLogs />
    </div>
  );
}
