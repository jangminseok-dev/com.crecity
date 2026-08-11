"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";

import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { ApiError, apiFetch } from "@/lib/api";
import { formatKrw } from "@/lib/labels";

type PendingWithdrawal = {
  id: number;
  creator_user_id: number;
  amount_krw: number;
  tax_krw: number;
  payout_krw: number;
  bank_name: string;
  account_number: string;
  account_holder: string;
  status: string;
  created_at: string | null;
};

/** 인출 운영 처리 — 운영자가 은행 이체 후 완료/실패를 확정한다(withdrawal.settle 권한). */
export default function AdminWithdrawals() {
  const queryClient = useQueryClient();
  // 단일 값 상태 — 처리 실패 메시지
  const [error, setError] = useState<string | null>(null);

  const { data: pending } = useQuery({
    queryKey: ["pendingWithdrawals"],
    queryFn: () => apiFetch<PendingWithdrawal[]>("/admin/withdrawals/pending"),
  });

  const settle = useMutation({
    mutationFn: ({ id, complete }: { id: number; complete: boolean }) =>
      apiFetch(`/admin/withdrawals/${id}/${complete ? "complete" : "fail"}`, { method: "POST" }),
    onSuccess: async () => {
      setError(null);
      await queryClient.invalidateQueries({ queryKey: ["pendingWithdrawals"] });
    },
    onError: (err) => setError(err instanceof ApiError ? err.detail : "처리에 실패했습니다."),
  });

  return (
    <section className="mt-12">
      <h2 className="text-xl font-bold tracking-[-0.02em]">인출 처리</h2>
      <p className="mt-1 text-sm text-muted-foreground">
        실지급액을 계좌로 이체한 뒤 "지급 완료"를 눌러 확정하세요. 실패 처리하면 크리에이터
        잔액이 복원됩니다.
      </p>
      {error && <p className="mt-3 text-sm text-destructive">{error}</p>}
      <div className="mt-4 grid gap-3">
        {!pending || pending.length === 0 ? (
          <p className="rounded-xl border border-dashed py-10 text-center text-sm text-muted-foreground">
            대기 중인 인출 요청이 없습니다.
          </p>
        ) : (
          pending.map((withdrawal) => (
            <Card key={withdrawal.id}>
              <CardContent className="flex flex-wrap items-center gap-4 p-5">
                <div className="min-w-0 flex-1">
                  <p className="font-semibold">
                    실지급 {formatKrw(withdrawal.payout_krw)}
                    <span className="ml-2 text-sm font-normal text-muted-foreground">
                      (요청 {formatKrw(withdrawal.amount_krw)} · 원천징수 {formatKrw(withdrawal.tax_krw)})
                    </span>
                  </p>
                  <p className="mt-1 text-sm text-muted-foreground">
                    {withdrawal.bank_name} {withdrawal.account_number} ({withdrawal.account_holder})
                    · user #{withdrawal.creator_user_id}
                    {withdrawal.created_at &&
                      ` · ${new Date(withdrawal.created_at).toLocaleString("ko-KR")}`}
                  </p>
                </div>
                <div className="flex shrink-0 gap-2">
                  <Button
                    size="sm"
                    disabled={settle.isPending}
                    onClick={() => settle.mutate({ id: withdrawal.id, complete: true })}
                  >
                    지급 완료
                  </Button>
                  <Button
                    size="sm"
                    variant="outline"
                    disabled={settle.isPending}
                    onClick={() => settle.mutate({ id: withdrawal.id, complete: false })}
                  >
                    이체 실패
                  </Button>
                </div>
              </CardContent>
            </Card>
          ))
        )}
      </div>
    </section>
  );
}
