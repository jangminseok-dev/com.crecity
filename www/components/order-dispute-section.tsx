"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { ApiError, apiFetch } from "@/lib/api";
import type { Dispute } from "@/lib/types";

const RESOLUTION_LABELS: Record<string, string> = {
  REFUND: "브랜드 전액 환불로 종결",
  RELEASE: "크리에이터 전액 지급으로 종결",
  DISMISS: "기각 — 주문 계속 진행",
};

/** 분쟁 신고·이력 — 합의가 안 될 때 운영자 중재를 요청한다(갭 #4). */
export default function OrderDisputeSection({
  orderId,
  canRaise,
}: {
  orderId: number;
  canRaise: boolean;
}) {
  const queryClient = useQueryClient();

  const { data: disputes } = useQuery({
    queryKey: ["disputes", orderId],
    queryFn: () => apiFetch<Dispute[]>(`/order/orders/${orderId}/disputes`),
  });

  const raise = useMutation({
    mutationFn: (reason: string) =>
      apiFetch<Dispute>(`/order/orders/${orderId}/disputes`, {
        method: "POST",
        body: JSON.stringify({ reason }),
      }),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["disputes", orderId] });
      await queryClient.invalidateQueries({ queryKey: ["order", orderId] });
    },
  });

  const handleSubmit = (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    const formElement = e.currentTarget;
    const reason = String(new FormData(formElement).get("reason") ?? "").trim();
    if (!reason) return;
    raise.mutate(reason, { onSuccess: () => formElement.reset() });
  };

  const open = disputes?.find((dispute) => dispute.status === "OPEN");
  if (!canRaise && (disputes?.length ?? 0) === 0) return null;

  return (
    <Card>
      <CardContent className="grid gap-4 p-6">
        <div>
          <p className="font-semibold">분쟁 중재</p>
          <p className="mt-1 text-sm text-muted-foreground">
            {open
              ? "운영자가 검토 중입니다 — 판정 전까지 검토 마감 자동 승인은 보류됩니다."
              : "합의가 어려우면 운영자 중재를 요청할 수 있습니다. 판정은 전액 환불 또는 전액 지급 중 하나입니다."}
          </p>
        </div>

        {(disputes?.length ?? 0) > 0 && (
          <ul className="grid gap-2">
            {disputes?.map((dispute) => (
              <li key={dispute.id} className="rounded-md border px-3 py-2 text-sm">
                <p className="whitespace-pre-wrap">{dispute.reason}</p>
                <p className="mt-1 text-xs text-muted-foreground">
                  {dispute.status === "OPEN"
                    ? "처리 대기 중"
                    : (dispute.resolution && RESOLUTION_LABELS[dispute.resolution]) ?? "처리 완료"}
                  {dispute.created_at &&
                    ` · ${new Date(dispute.created_at).toLocaleString("ko-KR")}`}
                </p>
              </li>
            ))}
          </ul>
        )}

        {canRaise && !open && (
          <form onSubmit={handleSubmit} className="grid gap-2">
            <textarea
              name="reason"
              rows={3}
              maxLength={2000}
              placeholder="무슨 일이 있었는지 구체적으로 적어 주세요 (10자 이상) — 운영자가 이 내용과 납품물을 근거로 판정합니다."
              className="rounded-md border border-input bg-transparent px-3 py-2 text-sm outline-none transition-colors focus:border-primary"
            />
            <Button
              type="submit"
              variant="outline"
              className="justify-self-start"
              disabled={raise.isPending}
            >
              분쟁 신고
            </Button>
            {raise.error && (
              <p className="text-sm text-destructive">
                {raise.error instanceof ApiError ? raise.error.detail : "신고에 실패했습니다."}
              </p>
            )}
          </form>
        )}
      </CardContent>
    </Card>
  );
}
