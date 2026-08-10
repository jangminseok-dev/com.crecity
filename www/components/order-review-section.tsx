"use client";

import { useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { z } from "zod";

import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { ApiError, apiFetch } from "@/lib/api";

type OrderReview = {
  id: number;
  communication_score: number;
  timeliness_score: number;
  satisfaction_score: number;
  overall_score: number;
  comment: string;
};

const reviewSchema = z.object({
  communication_score: z.coerce.number().int().min(1).max(5),
  timeliness_score: z.coerce.number().int().min(1).max(5),
  satisfaction_score: z.coerce.number().int().min(1).max(5),
  comment: z.string().min(5, "리뷰를 5자 이상 작성해 주세요."),
});

const SCORE_FIELDS = [
  { name: "communication_score", label: "소통" },
  { name: "timeliness_score", label: "기한 준수" },
  { name: "satisfaction_score", label: "만족도" },
] as const;

async function fetchOrderReview(orderId: number): Promise<OrderReview | null> {
  try {
    return await apiFetch<OrderReview>(`/review/orders/${orderId}/review`);
  } catch (error) {
    if (error instanceof ApiError && error.status === 404) return null;
    throw error;
  }
}

/** 구매 확정(COMPLETED) 주문의 브랜드에게만 렌더된다 — 주문당 1회 작성. */
export default function OrderReviewSection({ orderId }: { orderId: number }) {
  const queryClient = useQueryClient();
  // 단일 객체 상태 — 제출 진행·오류 (입력값은 FormData 패턴)
  const [form, setForm] = useState<{ submitting: boolean; error: string | null }>({
    submitting: false,
    error: null,
  });

  const { data: review, isPending } = useQuery({
    queryKey: ["orderReview", orderId],
    queryFn: () => fetchOrderReview(orderId),
  });

  if (isPending) return null;

  if (review) {
    return (
      <Card>
        <CardContent className="grid gap-2 p-5">
          <p className="font-semibold">내가 남긴 리뷰 ⭐ {review.overall_score}</p>
          <p className="text-sm text-muted-foreground">
            소통 {review.communication_score} · 기한 {review.timeliness_score} · 만족{" "}
            {review.satisfaction_score}
          </p>
          <p className="whitespace-pre-line text-sm">{review.comment}</p>
        </CardContent>
      </Card>
    );
  }

  const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    const parsed = reviewSchema.safeParse(Object.fromEntries(new FormData(e.currentTarget).entries()));
    if (!parsed.success) {
      setForm({ submitting: false, error: parsed.error.issues[0].message });
      return;
    }
    setForm({ submitting: true, error: null });
    try {
      await apiFetch(`/review/orders/${orderId}/review`, {
        method: "POST",
        body: JSON.stringify(parsed.data),
      });
      await queryClient.invalidateQueries({ queryKey: ["orderReview", orderId] });
    } catch (error) {
      setForm({
        submitting: false,
        error: error instanceof ApiError ? error.detail : "리뷰 등록에 실패했습니다.",
      });
    }
  };

  return (
    <Card>
      <CardContent className="p-5">
        <p className="font-semibold">거래는 어떠셨나요?</p>
        <p className="mt-1 text-sm text-muted-foreground">
          리뷰는 크리에이터 프로필에 공개되며 다른 브랜드의 선택을 돕습니다.
        </p>
        <form onSubmit={handleSubmit} className="mt-4 grid gap-4">
          <div className="grid grid-cols-3 gap-3">
            {SCORE_FIELDS.map((field) => (
              <div key={field.name} className="grid gap-1.5">
                <Label htmlFor={field.name}>{field.label}</Label>
                <select
                  id={field.name}
                  name={field.name}
                  defaultValue="5"
                  className="h-9 rounded-md border border-input bg-transparent px-3 text-sm"
                >
                  {[5, 4, 3, 2, 1].map((score) => (
                    <option key={score} value={score}>
                      {"⭐".repeat(score)} ({score})
                    </option>
                  ))}
                </select>
              </div>
            ))}
          </div>
          <div className="grid gap-1.5">
            <Label htmlFor="comment">리뷰</Label>
            <Textarea
              id="comment"
              name="comment"
              rows={3}
              placeholder="협업 과정과 결과물은 어땠나요?"
            />
          </div>
          {form.error && <p className="text-sm text-destructive">{form.error}</p>}
          <Button type="submit" disabled={form.submitting} className="justify-self-start">
            {form.submitting ? "등록 중…" : "리뷰 등록"}
          </Button>
        </form>
      </CardContent>
    </Card>
  );
}
