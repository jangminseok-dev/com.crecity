"use client";

import Link from "next/link";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";

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
};

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
      <h1 className="text-2xl font-bold tracking-[-0.02em]">프로필 심사</h1>
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

      {(user?.permissions.includes("withdrawal.settle") ?? false) && <AdminWithdrawals />}
    </div>
  );
}
