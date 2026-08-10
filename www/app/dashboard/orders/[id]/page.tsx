"use client";

import { useParams } from "next/navigation";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Separator } from "@/components/ui/separator";
import { Skeleton } from "@/components/ui/skeleton";
import { ApiError, apiFetch } from "@/lib/api";
import { useAuthStore } from "@/lib/auth-store";
import { ORDER_STATUS_LABELS, formatDeadline, formatKrw } from "@/lib/labels";
import type { Order } from "@/lib/types";

type TransitionAction = {
  path: string;
  label: string;
  confirm?: string;
  variant?: "default" | "outline" | "destructive";
};

/** 역할·상태에 따라 지금 가능한 액션 — 규칙의 정본은 백엔드 도메인이고 UI는 안내만 한다. */
function availableActions(order: Order, userId: number): TransitionAction[] {
  const isCreator = order.creator_user_id === userId;
  const isBrand = order.brand_user_id === userId;
  if (isCreator && order.status === "PENDING_ACCEPT") {
    return [
      { path: "accept", label: "주문 수락" },
      {
        path: "reject",
        label: "거절 (환불)",
        variant: "destructive",
        confirm: "주문을 거절하면 브랜드에게 전액 환불됩니다. 거절할까요?",
      },
    ];
  }
  if (isCreator && order.status === "IN_PROGRESS") {
    return [
      {
        path: "submit",
        label: "콘텐츠 제출",
        confirm: "제출하면 브랜드 검토가 시작됩니다(72시간 내 무응답 시 자동 승인). 제출할까요?",
      },
    ];
  }
  if (isBrand && order.status === "IN_REVIEW") {
    return [
      {
        path: "approve",
        label: "승인 (구매 확정)",
        confirm: "승인하면 크리에이터에게 대금이 적립되고 주문이 완료됩니다. 승인할까요?",
      },
      { path: "request-revision", label: "수정 요청", variant: "outline" },
    ];
  }
  return [];
}

export default function OrderDetailPage() {
  const { id } = useParams<{ id: string }>();
  const user = useAuthStore((s) => s.user);
  const queryClient = useQueryClient();
  // 단일 값 상태 — 전이 실패 메시지
  const [actionError, setActionError] = useState<string | null>(null);

  const { data: order, isPending, error } = useQuery({
    queryKey: ["order", id],
    queryFn: () => apiFetch<Order>(`/order/orders/${id}`),
  });

  const transition = useMutation({
    mutationFn: (path: string) =>
      apiFetch<Order>(`/order/orders/${id}/${path}`, { method: "POST" }),
    onSuccess: async () => {
      setActionError(null);
      await queryClient.invalidateQueries({ queryKey: ["order", id] });
      await queryClient.invalidateQueries({ queryKey: ["myOrders"] });
    },
    onError: (mutationError) => {
      setActionError(
        mutationError instanceof ApiError ? mutationError.detail : "처리에 실패했습니다.",
      );
    },
  });

  if (isPending || !user) return <Skeleton className="h-64 w-full" />;
  if (error || !order) {
    return (
      <p className="py-16 text-center text-muted-foreground">
        {error instanceof ApiError ? error.detail : "주문을 불러올 수 없습니다."}
      </p>
    );
  }

  const isBrand = order.brand_user_id === user.id;
  const actions = availableActions(order, user.id);

  return (
    <div className="grid gap-6">
      <div className="flex items-center gap-2">
        <h2 className="text-xl font-bold">주문 #{order.id}</h2>
        <Badge variant={order.status === "COMPLETED" ? "secondary" : "outline"}>
          {ORDER_STATUS_LABELS[order.status]}
        </Badge>
      </div>

      <Card>
        <CardContent className="grid gap-4 p-6">
          <div>
            <p className="text-sm text-muted-foreground">패키지</p>
            <p className="mt-1 font-medium">{order.package_title}</p>
          </div>
          <Separator />
          <div>
            <p className="text-sm text-muted-foreground">요구사항</p>
            <p className="mt-1 whitespace-pre-line text-sm">{order.requirements}</p>
          </div>
          <Separator />
          <div className="grid grid-cols-2 gap-4 text-sm">
            <div>
              <p className="text-muted-foreground">패키지 가격</p>
              <p className="mt-1 font-semibold">{formatKrw(order.amount_krw)}</p>
            </div>
            {isBrand ? (
              <div>
                <p className="text-muted-foreground">
                  결제 총액 (수수료 {order.brand_fee_percent}% 포함 · 에스크로 보관)
                </p>
                <p className="mt-1 font-semibold">{formatKrw(order.brand_total_krw)}</p>
              </div>
            ) : (
              <div>
                <p className="text-muted-foreground">
                  정산 예정액 (수수료 {order.creator_fee_percent}% 제외)
                </p>
                <p className="mt-1 font-semibold">{formatKrw(order.creator_payout_krw)}</p>
              </div>
            )}
          </div>
          {order.deadline_at && (
            <p className="rounded-md bg-muted p-3 text-sm text-muted-foreground">
              ⏰ {order.status === "PENDING_ACCEPT" ? "수락 마감" : "검토 마감"}:{" "}
              {formatDeadline(order.deadline_at)}
              {order.status === "IN_REVIEW" && " — 지나면 자동 승인됩니다"}
              {order.status === "PENDING_ACCEPT" && " — 지나면 자동 환불됩니다"}
            </p>
          )}
        </CardContent>
      </Card>

      {actions.length > 0 && (
        <div className="grid gap-2">
          <div className="flex gap-2">
            {actions.map((action) => (
              <Button
                key={action.path}
                variant={action.variant ?? "default"}
                disabled={transition.isPending}
                onClick={() => {
                  if (!action.confirm || window.confirm(action.confirm)) {
                    transition.mutate(action.path);
                  }
                }}
              >
                {action.label}
              </Button>
            ))}
          </div>
          {actionError && <p className="text-sm text-destructive">{actionError}</p>}
        </div>
      )}

      {order.status === "COMPLETED" && (
        <p className="rounded-md bg-muted p-3 text-sm text-muted-foreground">
          구매가 확정된 주문입니다 —{" "}
          {isBrand ? "크리에이터에게 대금이 적립되었습니다." : "잔액 탭에서 적립금을 확인하세요."}
        </p>
      )}
      {order.status === "REFUNDED" && (
        <p className="rounded-md bg-muted p-3 text-sm text-muted-foreground">
          환불된 주문입니다 — {isBrand ? "크레딧 탭에서 환불 금액을 확인하세요." : "브랜드에게 전액 환불되었습니다."}
        </p>
      )}
    </div>
  );
}
