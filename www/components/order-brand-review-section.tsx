"use client";

import { useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { z } from "zod";

import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { ApiError, apiFetch } from "@/lib/api";

type BrandReview = {
  id: number;
  score: number;
  comment: string;
};

const brandReviewSchema = z.object({
  score: z.coerce.number().int().min(1).max(5),
  comment: z.string().min(1, "코멘트를 작성해 주세요."),
});

async function fetchBrandReview(orderId: number): Promise<BrandReview | null> {
  try {
    return await apiFetch<BrandReview>(`/review/orders/${orderId}/brand-review`);
  } catch (error) {
    if (error instanceof ApiError && error.status === 404) return null;
    throw error;
  }
}

/** 브랜드 평가(갭 #83) — 구매 확정(COMPLETED) 주문의 크리에이터에게만 렌더된다. 주문당 1회. */
export default function OrderBrandReviewSection({ orderId }: { orderId: number }) {
  const queryClient = useQueryClient();
  // 단일 객체 상태 — 제출 진행·오류 (입력값은 FormData 패턴)
  const [form, setForm] = useState<{ submitting: boolean; error: string | null }>({
    submitting: false,
    error: null,
  });

  const { data: review, isPending } = useQuery({
    queryKey: ["orderBrandReview", orderId],
    queryFn: () => fetchBrandReview(orderId),
  });

  if (isPending) return null;

  if (review) {
    return (
      <Card>
        <CardContent className="grid gap-2 p-5">
          <p className="font-semibold">내가 남긴 브랜드 평가 ⭐ {review.score}</p>
          <p className="whitespace-pre-line text-sm">{review.comment}</p>
          <p className="text-xs text-muted-foreground">
            평점은 집계에만 반영되고 코멘트는 공개되지 않습니다.
          </p>
        </CardContent>
      </Card>
    );
  }

  const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    const parsed = brandReviewSchema.safeParse(
      Object.fromEntries(new FormData(e.currentTarget).entries()),
    );
    if (!parsed.success) {
      setForm({ submitting: false, error: parsed.error.issues[0].message });
      return;
    }
    setForm({ submitting: true, error: null });
    try {
      await apiFetch(`/review/orders/${orderId}/brand-review`, {
        method: "POST",
        body: JSON.stringify(parsed.data),
      });
      await queryClient.invalidateQueries({ queryKey: ["orderBrandReview", orderId] });
    } catch (error) {
      setForm({
        submitting: false,
        error: error instanceof ApiError ? error.detail : "평가 등록에 실패했습니다.",
      });
    }
  };

  return (
    <Card>
      <CardContent className="p-5">
        <p className="font-semibold">이 브랜드와의 거래는 어떠셨나요?</p>
        <p className="mt-1 text-sm text-muted-foreground">
          평점 집계(평균·건수)만 공개됩니다 — 코멘트 원문은 공개되지 않으며, 다른
          크리에이터가 주문 수락을 판단할 때 참고합니다.
        </p>
        <form onSubmit={handleSubmit} className="mt-4 grid gap-4">
          <div className="grid gap-1.5">
            <Label htmlFor="score">종합 평점</Label>
            <select
              id="score"
              name="score"
              defaultValue="5"
              className="h-9 w-40 rounded-md border border-input bg-transparent px-3 text-sm"
            >
              {[5, 4, 3, 2, 1].map((score) => (
                <option key={score} value={score}>
                  {"⭐".repeat(score)} ({score})
                </option>
              ))}
            </select>
          </div>
          <div className="grid gap-1.5">
            <Label htmlFor="comment">코멘트</Label>
            <Textarea
              id="comment"
              name="comment"
              rows={3}
              placeholder="소통·피드백·정산 과정은 어땠나요?"
            />
          </div>
          {form.error && <p className="text-sm text-destructive">{form.error}</p>}
          <Button type="submit" disabled={form.submitting} className="justify-self-start">
            {form.submitting ? "등록 중…" : "브랜드 평가 등록"}
          </Button>
        </form>
      </CardContent>
    </Card>
  );
}
