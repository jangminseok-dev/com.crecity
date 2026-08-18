"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";

import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Textarea } from "@/components/ui/textarea";
import { ApiError, apiFetch } from "@/lib/api";

type RevisionRequest = {
  id: number;
  requested_in: "DRAFT_REVIEW" | "IN_REVIEW";
  comment: string;
  created_at: string | null;
};

/** 수정 요청 이력 + 요청 폼(갭 #84) — 피드백 본문이 주문에 남아 재작업·분쟁의 근거가 된다. */
export default function OrderRevisionsSection({
  orderId,
  canRequest,
  revisionsLeft,
}: {
  orderId: number;
  canRequest: boolean;
  revisionsLeft: number;
}) {
  const queryClient = useQueryClient();
  // 단일 객체 상태 — 폼 열림·오류 (본문은 FormData 패턴)
  const [state, setState] = useState<{ open: boolean; error: string | null }>({
    open: false,
    error: null,
  });

  const { data: revisions } = useQuery({
    queryKey: ["orderRevisions", orderId],
    queryFn: () => apiFetch<RevisionRequest[]>(`/order/orders/${orderId}/revisions`),
  });

  const request = useMutation({
    mutationFn: (comment: string) =>
      apiFetch(`/order/orders/${orderId}/request-revision`, {
        method: "POST",
        body: JSON.stringify({ comment }),
      }),
    onSuccess: async () => {
      setState({ open: false, error: null });
      await queryClient.invalidateQueries({ queryKey: ["order", String(orderId)] });
      await queryClient.invalidateQueries({ queryKey: ["orderRevisions", orderId] });
    },
    onError: (error) =>
      setState((prev) => ({
        ...prev,
        error: error instanceof ApiError ? error.detail : "수정 요청에 실패했습니다.",
      })),
  });

  const showRequestButton = canRequest && revisionsLeft > 0;
  if (!showRequestButton && (!revisions || revisions.length === 0)) return null;

  return (
    <Card>
      <CardContent className="grid gap-3 p-6">
        <p className="font-semibold">수정 요청</p>

        {revisions && revisions.length > 0 && (
          <div className="grid gap-2">
            {revisions.map((item, index) => (
              <div key={item.id} className="rounded-lg bg-muted p-3 text-sm">
                <p className="text-xs text-muted-foreground">
                  {index + 1}회차 · {item.requested_in === "DRAFT_REVIEW" ? "초안 검토" : "최종 검토"}
                  {item.created_at && ` · ${new Date(item.created_at).toLocaleString("ko-KR")}`}
                </p>
                <p className="mt-1 whitespace-pre-line">{item.comment}</p>
              </div>
            ))}
          </div>
        )}

        {showRequestButton && !state.open && (
          <Button
            variant="outline"
            size="sm"
            className="justify-self-start"
            onClick={() => setState({ open: true, error: null })}
          >
            수정 요청 (남은 횟수 {revisionsLeft}회)
          </Button>
        )}

        {showRequestButton && state.open && (
          <form
            className="grid gap-2"
            onSubmit={(event) => {
              event.preventDefault();
              const comment = String(new FormData(event.currentTarget).get("comment") ?? "").trim();
              if (comment.length < 5) {
                setState((prev) => ({ ...prev, error: "수정할 내용을 5자 이상 적어 주세요." }));
                return;
              }
              request.mutate(comment);
            }}
          >
            <Textarea
              name="comment"
              rows={3}
              maxLength={2000}
              placeholder="무엇을 어떻게 고쳐야 하는지 구체적으로 적어 주세요 — 크리에이터에게 그대로 전달됩니다."
            />
            {state.error && <p className="text-sm text-destructive">{state.error}</p>}
            <div className="flex gap-2">
              <Button type="submit" size="sm" disabled={request.isPending}>
                {request.isPending ? "요청 중…" : "수정 요청 보내기"}
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
        )}
      </CardContent>
    </Card>
  );
}
