"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import PayoutStatement from "@/components/payout-statement";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Skeleton } from "@/components/ui/skeleton";
import { ApiError, apiFetch } from "@/lib/api";
import { useAuthStore } from "@/lib/auth-store";
import { formatKrw } from "@/lib/labels";
import type { Balance } from "@/lib/types";

type Withdrawal = {
  id: number;
  amount_krw: number;
  tax_krw: number;
  payout_krw: number;
  bank_name: string;
  account_number: string;
  account_holder: string;
  status: "REQUESTED" | "PAID" | "FAILED";
  created_at: string | null;
  settled_at: string | null;
};

const WITHDRAWAL_STATUS: Record<Withdrawal["status"], { label: string; className: string }> = {
  REQUESTED: { label: "이체 대기", className: "bg-[#fef3e0] text-[#c07908]" },
  PAID: { label: "지급 완료", className: "bg-[#e6f7f0] text-[#0fa066]" },
  FAILED: { label: "이체 실패(복원됨)", className: "bg-[#fdebec] text-[#e5484d]" },
};

function WithdrawalSection({ balanceKrw }: { balanceKrw: number }) {
  const queryClient = useQueryClient();
  const { data: withdrawals } = useQuery({
    queryKey: ["myWithdrawals"],
    queryFn: () => apiFetch<Withdrawal[]>("/order/withdrawals"),
  });

  const request = useMutation({
    mutationFn: (form: FormData) =>
      apiFetch<Withdrawal>("/order/withdrawals", {
        method: "POST",
        body: JSON.stringify({
          amount_krw: Number(form.get("amount_krw")),
          bank_name: String(form.get("bank_name") ?? ""),
          account_number: String(form.get("account_number") ?? ""),
          account_holder: String(form.get("account_holder") ?? ""),
        }),
      }),
    onSuccess: async () => {
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ["myWithdrawals"] }),
        queryClient.invalidateQueries({ queryKey: ["myBalance"] }),
      ]);
    },
  });

  const handleSubmit = (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    const formElement = e.currentTarget;
    request.mutate(new FormData(formElement), { onSuccess: () => formElement.reset() });
  };

  return (
    <>
      <Card className="mt-4">
        <CardContent className="p-6">
          <h2 className="font-semibold">인출 요청</h2>
          <p className="mt-1 text-sm text-muted-foreground">
            원천징수 3.3%를 제외한 금액이 입금됩니다. 이체는 영업일 기준 순차 처리돼요.
          </p>
          <form onSubmit={handleSubmit} className="mt-4 grid gap-4">
            <div className="grid gap-1.5">
              <Label htmlFor="amount_krw">인출 금액 (원)</Label>
              <Input
                id="amount_krw"
                name="amount_krw"
                type="number"
                min={1}
                max={balanceKrw}
                placeholder={`최대 ${formatKrw(balanceKrw)}`}
                required
              />
            </div>
            <div className="grid gap-4 sm:grid-cols-3">
              <div className="grid gap-1.5">
                <Label htmlFor="bank_name">은행명</Label>
                <Input id="bank_name" name="bank_name" placeholder="국민은행" required />
              </div>
              <div className="grid gap-1.5">
                <Label htmlFor="account_number">계좌번호</Label>
                <Input id="account_number" name="account_number" placeholder="000-000-000000" required />
              </div>
              <div className="grid gap-1.5">
                <Label htmlFor="account_holder">예금주</Label>
                <Input id="account_holder" name="account_holder" placeholder="홍길동" required />
              </div>
            </div>
            {request.error && (
              <p className="text-sm text-destructive">
                {request.error instanceof ApiError ? request.error.detail : "인출 요청에 실패했습니다."}
              </p>
            )}
            <Button type="submit" disabled={request.isPending || balanceKrw <= 0}>
              {request.isPending ? "요청 중…" : "인출 요청하기"}
            </Button>
          </form>
        </CardContent>
      </Card>

      {withdrawals && withdrawals.length > 0 && (
        <div className="mt-6">
          <h2 className="font-semibold">인출 내역</h2>
          <div className="mt-2">
            {withdrawals.map((withdrawal) => {
              const status = WITHDRAWAL_STATUS[withdrawal.status];
              return (
                <div key={withdrawal.id} className="flex items-center gap-4 border-b py-3.5">
                  <div className="min-w-0 flex-1">
                    <p className="text-sm font-semibold">
                      {formatKrw(withdrawal.amount_krw)}
                      <span className="ml-2 font-normal text-muted-foreground">
                        실지급 {formatKrw(withdrawal.payout_krw)} (세액 {formatKrw(withdrawal.tax_krw)})
                      </span>
                    </p>
                    <p className="mt-0.5 text-[13px] text-muted-foreground">
                      {withdrawal.bank_name} {withdrawal.account_number} ({withdrawal.account_holder})
                      {withdrawal.created_at &&
                        ` · ${new Date(withdrawal.created_at).toLocaleDateString("ko-KR")}`}
                    </p>
                  </div>
                  <span
                    className={`inline-flex h-6 shrink-0 items-center whitespace-nowrap rounded-md px-2 text-xs font-semibold ${status.className}`}
                  >
                    {status.label}
                  </span>
                </div>
              );
            })}
          </div>
        </div>
      )}
    </>
  );
}

export default function DashboardBalancePage() {
  const user = useAuthStore((s) => s.user);
  const { data: balance, isPending } = useQuery({
    queryKey: ["myBalance"],
    queryFn: () => apiFetch<Balance>("/order/balance"),
  });

  if (isPending || !user) return <Skeleton className="h-40 w-full" />;
  const isCreator = user.account_type === "CREATOR";
  const balanceKrw = balance?.balance_krw ?? 0;

  return (
    <div>
      <Card>
        <CardContent className="p-6">
          <p className="text-sm text-muted-foreground">
            {isCreator ? "적립금 (구매 확정된 주문의 정산액)" : "크레딧 (환불된 주문 금액)"}
          </p>
          <p className="mt-2 text-[32px] font-bold tracking-[-0.02em]">{formatKrw(balanceKrw)}</p>
          {!isCreator && (
            <p className="mt-3 text-sm text-muted-foreground">
              새 주문 결제 시 &quot;보유 크레딧 사용&quot;을 체크하면 이 금액이 자동으로
              차감됩니다. 잔액이 결제 총액 이상이면 카드 결제 없이 바로 주문됩니다.
            </p>
          )}
        </CardContent>
      </Card>
      {isCreator && (
        <>
          <WithdrawalSection balanceKrw={balanceKrw} />
          <PayoutStatement />
        </>
      )}
    </div>
  );
}
