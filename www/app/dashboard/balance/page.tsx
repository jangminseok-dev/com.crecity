"use client";

import { useQuery } from "@tanstack/react-query";

import { Card, CardContent } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { apiFetch } from "@/lib/api";
import { useAuthStore } from "@/lib/auth-store";
import { formatKrw } from "@/lib/labels";
import type { Balance } from "@/lib/types";

export default function DashboardBalancePage() {
  const user = useAuthStore((s) => s.user);
  const { data: balance, isPending } = useQuery({
    queryKey: ["myBalance"],
    queryFn: () => apiFetch<Balance>("/order/balance"),
  });

  if (isPending || !user) return <Skeleton className="h-40 w-full" />;
  const isCreator = user.account_type === "CREATOR";

  return (
    <Card>
      <CardContent className="p-6">
        <p className="text-sm text-muted-foreground">
          {isCreator ? "적립금 (구매 확정된 주문의 정산액)" : "크레딧 (환불된 주문 금액)"}
        </p>
        <p className="mt-2 text-3xl font-bold">{formatKrw(balance?.balance_krw ?? 0)}</p>
        <p className="mt-3 text-sm text-muted-foreground">
          {isCreator
            ? "인출 기능은 결제(PG) 연동과 함께 제공될 예정입니다."
            : "크레딧으로 새 주문을 결제하는 기능은 결제(PG) 연동과 함께 제공될 예정입니다."}
        </p>
      </CardContent>
    </Card>
  );
}
