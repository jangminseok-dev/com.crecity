"use client";

import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";

import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { ApiError, apiFetch } from "@/lib/api";

/**
 * 주문 수신 켜기·끄기(갭 #64).
 *
 * 무응답 72시간은 랭킹 페널티(갭 #32)로 이어지므로, 쉬는 동안 스스로 닫을 수단이 필요하다.
 */
export default function OrderAcceptanceToggle({ accepting }: { accepting: boolean }) {
  const queryClient = useQueryClient();
  // 단일 값 상태 — 전환 실패 메시지
  const [error, setError] = useState<string | null>(null);

  const mutation = useMutation({
    mutationFn: (next: boolean) =>
      apiFetch("/creator/my/profile/accepting-orders", {
        method: "PUT",
        body: JSON.stringify({ accepting: next }),
      }),
    onSuccess: async () => {
      setError(null);
      await queryClient.invalidateQueries({ queryKey: ["myProfile"] });
    },
    onError: (err) =>
      setError(err instanceof ApiError ? err.detail : "변경에 실패했습니다."),
  });

  return (
    <Card className={accepting ? undefined : "border-destructive/40 bg-destructive/5"}>
      <CardContent className="flex flex-wrap items-center justify-between gap-3 p-5">
        <div>
          <h3 className="font-semibold">
            {accepting ? "주문을 받는 중" : "주문을 받지 않는 중"}
          </h3>
          <p className="mt-1 text-sm text-muted-foreground">
            {accepting
              ? "휴가·마감으로 응답이 어려우면 잠시 꺼 두세요. 무응답으로 72시간이 지나면 인기 순위에 불이익이 있습니다."
              : "목록에 노출되지 않고 새 주문도 들어오지 않습니다. 진행 중인 주문에는 영향이 없습니다."}
          </p>
          {error && <p className="mt-2 text-sm text-destructive">{error}</p>}
        </div>
        <Button
          variant={accepting ? "outline" : "default"}
          size="sm"
          disabled={mutation.isPending}
          onClick={() => mutation.mutate(!accepting)}
        >
          {mutation.isPending ? "변경 중…" : accepting ? "주문 잠시 중단" : "주문 다시 받기"}
        </Button>
      </CardContent>
    </Card>
  );
}
