"use client";

import Link from "next/link";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";

import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { Textarea } from "@/components/ui/textarea";
import { ApiError, apiFetch } from "@/lib/api";
import { useAuthStore } from "@/lib/auth-store";

type ReviewItem = {
  id: number;
  overall_score: number;
  comment: string | null;
  is_locked: boolean;
  created_at: string | null;
  reply: string | null;
  replied_at: string | null;
  can_reply: boolean;
};

type CreatorReviews = {
  total: number;
  average_overall: number | null;
  average_communication: number | null;
  average_timeliness: number | null;
  average_satisfaction: number | null;
  items: ReviewItem[];
};

/** 답글 작성(갭 #53) — 리뷰당 1회라 등록 후에는 폼이 사라진다. */
function ReplyForm({ reviewId, slug }: { reviewId: number; slug: string }) {
  const queryClient = useQueryClient();
  // 단일 객체 상태 — 열림 여부·오류 (본문은 FormData 패턴)
  const [state, setState] = useState<{ open: boolean; error: string | null }>({
    open: false,
    error: null,
  });

  const mutation = useMutation({
    mutationFn: (reply: string) =>
      apiFetch(`/review/reviews/${reviewId}/reply`, {
        method: "POST",
        body: JSON.stringify({ reply }),
      }),
    onSuccess: async () => {
      setState({ open: false, error: null });
      await queryClient.invalidateQueries({ queryKey: ["creatorReviews", slug] });
    },
    onError: (error) =>
      setState((prev) => ({
        ...prev,
        error: error instanceof ApiError ? error.detail : "답글 등록에 실패했습니다.",
      })),
  });

  if (!state.open) {
    return (
      <button
        type="button"
        onClick={() => setState({ open: true, error: null })}
        className="mt-2 text-[13px] font-medium text-primary hover:underline"
      >
        답글 남기기
      </button>
    );
  }

  return (
    <form
      className="mt-3 grid gap-2"
      onSubmit={(event) => {
        event.preventDefault();
        const reply = String(new FormData(event.currentTarget).get("reply") ?? "").trim();
        if (!reply) {
          setState((prev) => ({ ...prev, error: "답글 내용을 입력해 주세요." }));
          return;
        }
        mutation.mutate(reply);
      }}
    >
      <Textarea
        name="reply"
        rows={3}
        maxLength={1000}
        placeholder="리뷰에 대한 답글을 남겨 보세요. 한 번만 등록할 수 있습니다."
      />
      {state.error && <p className="text-sm text-destructive">{state.error}</p>}
      <div className="flex gap-2">
        <Button type="submit" size="sm" disabled={mutation.isPending}>
          {mutation.isPending ? "등록 중…" : "답글 등록"}
        </Button>
        <Button
          type="button"
          variant="outline"
          size="sm"
          onClick={() => setState({ open: false, error: null })}
        >
          취소
        </Button>
      </div>
    </form>
  );
}

/** 집계는 공개, 원문은 로그인 시에만(블러 정책 — collabstr Freemium Gate). */
export default function CreatorReviews({ slug }: { slug: string }) {
  // 공개 API라 토큰 없이도 200이 온다 — 세션 복원 전에 조회하면 로그인 상태인데도
  // 잠긴(블러) 응답이 캐시되고 401 재시도 경로도 타지 않는다. 복원이 끝날 때까지 기다리고,
  // 로그인 여부를 키에 넣어 로그인/로그아웃 시 다시 조회한다.
  const authStatus = useAuthStore((s) => s.status);
  const { data, isPending } = useQuery({
    queryKey: ["creatorReviews", slug, authStatus === "authenticated"],
    queryFn: () => apiFetch<CreatorReviews>(`/review/creators/${slug}`),
    enabled: authStatus !== "loading",
  });

  if (isPending) return <Skeleton className="h-32 w-full" />;
  if (!data || data.total === 0) {
    return (
      <p className="rounded-lg border border-dashed py-8 text-center text-sm text-muted-foreground">
        아직 리뷰가 없습니다 — 첫 거래를 완료하면 리뷰가 쌓입니다.
      </p>
    );
  }

  return (
    <div className="grid gap-4">
      <div className="flex flex-wrap items-center gap-4 rounded-lg bg-muted p-4">
        <p className="text-2xl font-bold">⭐ {data.average_overall}</p>
        <p className="text-sm text-muted-foreground">
          리뷰 {data.total}개 · 소통 {data.average_communication} · 기한{" "}
          {data.average_timeliness} · 만족 {data.average_satisfaction}
        </p>
      </div>
      <div className="grid gap-3">
        {data.items.map((item) => (
          <Card key={item.id}>
            <CardContent className="p-4">
              <p className="text-sm font-semibold">⭐ {item.overall_score}</p>
              {item.is_locked ? (
                <p className="mt-1 text-sm text-muted-foreground blur-[3px] select-none">
                  리뷰 원문은 로그인하면 볼 수 있습니다. 리뷰 원문은 로그인하면 볼 수 있습니다.
                </p>
              ) : (
                <p className="mt-1 whitespace-pre-line text-sm">{item.comment}</p>
              )}

              {/* 크리에이터 답글 — 원문이 잠기면 함께 잠긴다 */}
              {item.reply && (
                <div className="mt-3 rounded-lg bg-secondary p-3">
                  <p className="text-[13px] font-semibold">크리에이터 답글</p>
                  <p className="mt-1 whitespace-pre-line text-sm">{item.reply}</p>
                </div>
              )}
              {item.can_reply && <ReplyForm reviewId={item.id} slug={slug} />}
            </CardContent>
          </Card>
        ))}
      </div>
      {data.items.some((item) => item.is_locked) && (
        <p className="text-center text-sm text-muted-foreground">
          <Link href="/login" className="underline underline-offset-2">
            로그인하고 리뷰 원문 보기
          </Link>
        </p>
      )}
    </div>
  );
}
