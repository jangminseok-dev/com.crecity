"use client";

import Link from "next/link";
import { useQuery } from "@tanstack/react-query";

import { Card, CardContent } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { apiFetch } from "@/lib/api";

type CreatorReviews = {
  total: number;
  average_overall: number | null;
  average_communication: number | null;
  average_timeliness: number | null;
  average_satisfaction: number | null;
  items: {
    id: number;
    overall_score: number;
    comment: string | null;
    is_locked: boolean;
    created_at: string | null;
  }[];
};

/** 집계는 공개, 원문은 로그인 시에만(블러 정책 — collabstr Freemium Gate). */
export default function CreatorReviews({ slug }: { slug: string }) {
  const { data, isPending } = useQuery({
    queryKey: ["creatorReviews", slug],
    queryFn: () => apiFetch<CreatorReviews>(`/review/creators/${slug}`),
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
