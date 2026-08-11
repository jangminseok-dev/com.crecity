"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { loadTossPayments } from "@tosspayments/tosspayments-sdk";
import { useState } from "react";

import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { ApiError, apiFetch } from "@/lib/api";
import { formatKrw } from "@/lib/labels";
import type { OrderAdjustment } from "@/lib/types";

type CheckoutResponse = {
  pg_order_id: string;
  amount_krw: number;
  credit_applied_krw: number;
  pg_amount_krw: number;
  order_name: string;
  client_key: string;
};

const STATUS_LABELS: Record<OrderAdjustment["status"], string> = {
  REQUESTED: "결제 대기",
  PAID: "결제 완료 — 주문 금액 반영됨",
  DECLINED: "거절됨",
};

/** 진행 중 주문 금액 변경(§3.8·§6) — 크리에이터가 요청하고 브랜드가 추가 결제로 수락한다. */
export default function OrderAdjustmentSection({
  orderId,
  userId,
  isBrand,
  isCreator,
  canRequest,
}: {
  orderId: number;
  userId: number;
  isBrand: boolean;
  isCreator: boolean;
  canRequest: boolean;
}) {
  const queryClient = useQueryClient();
  // 단일 객체 상태 — 진행·오류 (입력값은 FormData 패턴)
  const [ui, setUi] = useState<{ paying: boolean; error: string | null }>({
    paying: false,
    error: null,
  });

  const { data: adjustments } = useQuery({
    queryKey: ["orderAdjustments", orderId],
    queryFn: () => apiFetch<OrderAdjustment[]>(`/order/orders/${orderId}/adjustments`),
  });

  const invalidate = async () => {
    await queryClient.invalidateQueries({ queryKey: ["orderAdjustments", orderId] });
    await queryClient.invalidateQueries({ queryKey: ["order", String(orderId)] });
  };

  const request = useMutation({
    mutationFn: (body: { extra_amount_krw: number; reason: string }) =>
      apiFetch<OrderAdjustment>(`/order/orders/${orderId}/adjustments`, {
        method: "POST",
        body: JSON.stringify(body),
      }),
    onSuccess: () => {
      setUi({ paying: false, error: null });
      void invalidate();
    },
    onError: (error) =>
      setUi({ paying: false, error: error instanceof ApiError ? error.detail : "요청에 실패했습니다." }),
  });

  const decline = useMutation({
    mutationFn: (adjustmentId: number) =>
      apiFetch<OrderAdjustment>(`/order/adjustments/${adjustmentId}/decline`, { method: "POST" }),
    onSuccess: invalidate,
  });

  const pay = async (adjustmentId: number) => {
    setUi({ paying: true, error: null });
    try {
      const checkout = await apiFetch<CheckoutResponse>("/payment/checkouts/adjustment", {
        method: "POST",
        body: JSON.stringify({ adjustment_id: adjustmentId, use_credit: false }),
      });
      if (checkout.pg_amount_krw === 0) {
        await apiFetch("/payment/confirm", {
          method: "POST",
          body: JSON.stringify({ payment_key: "", pg_order_id: checkout.pg_order_id, amount_krw: 0 }),
        });
        setUi({ paying: false, error: null });
        await invalidate();
        return;
      }
      const tossPayments = await loadTossPayments(checkout.client_key);
      const payment = tossPayments.payment({ customerKey: `crecity-user-${userId}` });
      await payment.requestPayment({
        method: "CARD",
        amount: { currency: "KRW", value: checkout.pg_amount_krw },
        orderId: checkout.pg_order_id,
        orderName: checkout.order_name,
        successUrl: `${window.location.origin}/orders/pay/success`,
        failUrl: `${window.location.origin}/orders/pay/fail`,
      });
    } catch (error) {
      setUi({
        paying: false,
        error:
          error instanceof ApiError
            ? error.detail
            : error instanceof Error && error.message
              ? error.message
              : "추가 결제에 실패했습니다.",
      });
    }
  };

  const handleSubmit = (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    const formElement = e.currentTarget;
    const form = new FormData(formElement);
    const extra = Number(form.get("extra_amount_krw"));
    const reason = String(form.get("reason") ?? "").trim();
    if (!extra || extra <= 0 || !reason) {
      setUi({ paying: false, error: "추가 금액과 사유를 입력해 주세요." });
      return;
    }
    request.mutate(
      { extra_amount_krw: extra, reason },
      { onSuccess: () => formElement.reset() },
    );
  };

  const pending = adjustments?.find((a) => a.status === "REQUESTED");
  const history = adjustments?.filter((a) => a.status !== "REQUESTED") ?? [];

  if (!adjustments || (adjustments.length === 0 && !canRequest)) return null;

  return (
    <Card>
      <CardContent className="grid gap-4 p-6">
        <div>
          <p className="font-semibold">추가 금액 요청</p>
          <p className="mt-1 text-sm text-muted-foreground">
            작업 범위가 늘어나면 크리에이터가 추가 금액을 요청하고, 브랜드가 결제하면 주문 금액에
            반영됩니다(추가분도 에스크로 보관).
          </p>
        </div>

        {pending && (
          <div className="rounded-xl border p-4">
            <div className="flex items-center justify-between gap-3">
              <p className="font-semibold">{formatKrw(pending.extra_amount_krw)} 추가 요청</p>
              <span className="text-[13px] text-muted-foreground">
                {STATUS_LABELS[pending.status]}
              </span>
            </div>
            <p className="mt-1.5 whitespace-pre-line text-sm text-muted-foreground">
              {pending.reason}
            </p>
            {isBrand && (
              <div className="mt-3 flex gap-2">
                <Button size="sm" disabled={ui.paying} onClick={() => pay(pending.id)}>
                  {ui.paying ? "결제창 여는 중…" : "추가 결제하기"}
                </Button>
                <Button
                  size="sm"
                  variant="outline"
                  disabled={decline.isPending}
                  onClick={() => decline.mutate(pending.id)}
                >
                  거절
                </Button>
              </div>
            )}
            {isCreator && (
              <p className="mt-3 text-[13px] text-muted-foreground">
                브랜드의 결제를 기다리는 중입니다.
              </p>
            )}
          </div>
        )}

        {history.length > 0 && (
          <ul className="grid gap-1.5 text-sm">
            {history.map((item) => (
              <li key={item.id} className="flex items-center justify-between gap-3">
                <span className="truncate text-muted-foreground">
                  {formatKrw(item.extra_amount_krw)} — {item.reason}
                </span>
                <span className="shrink-0 text-[13px] text-muted-foreground">
                  {STATUS_LABELS[item.status]}
                </span>
              </li>
            ))}
          </ul>
        )}

        {canRequest && !pending && (
          <form onSubmit={handleSubmit} className="grid gap-3">
            <div className="grid gap-1.5">
              <Label htmlFor="extra_amount_krw">추가 금액 (원)</Label>
              <input
                id="extra_amount_krw"
                name="extra_amount_krw"
                type="number"
                min={1}
                placeholder="100000"
                className="h-10 rounded-lg border border-input bg-transparent px-3 text-sm outline-none focus:border-primary"
              />
            </div>
            <div className="grid gap-1.5">
              <Label htmlFor="reason">사유</Label>
              <Textarea
                id="reason"
                name="reason"
                rows={2}
                maxLength={500}
                placeholder="요청하신 촬영 컷 2개가 원 범위를 넘어 추가 비용이 필요합니다."
              />
            </div>
            {ui.error && <p className="text-sm text-destructive">{ui.error}</p>}
            <Button type="submit" disabled={request.isPending} className="justify-self-start">
              {request.isPending ? "요청 중…" : "추가 금액 요청"}
            </Button>
          </form>
        )}
        {ui.error && !canRequest && <p className="text-sm text-destructive">{ui.error}</p>}
      </CardContent>
    </Card>
  );
}
