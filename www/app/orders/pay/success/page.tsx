"use client";

import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { Suspense, useEffect, useRef, useState } from "react";

import { Button } from "@/components/ui/button";
import { ApiError, apiFetch } from "@/lib/api";
import { useAuthStore } from "@/lib/auth-store";

type ConfirmState =
  | { phase: "confirming" }
  | { phase: "error"; message: string };

function PaySuccessContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const authStatus = useAuthStore((s) => s.status);
  // 단일 객체 상태 — 승인 단계·오류 메시지
  const [state, setState] = useState<ConfirmState>({ phase: "confirming" });
  // StrictMode 이중 실행 가드 — 승인 API는 반드시 1회만
  const startedRef = useRef(false);

  useEffect(() => {
    if (startedRef.current || authStatus === "loading") return;
    startedRef.current = true;

    const paymentKey = searchParams.get("paymentKey");
    const pgOrderId = searchParams.get("orderId");
    const amount = Number(searchParams.get("amount"));
    if (!paymentKey || !pgOrderId || !amount) {
      setState({ phase: "error", message: "결제 정보가 올바르지 않습니다." });
      return;
    }

    const confirm = async () => {
      try {
        const { order_id } = await apiFetch<{ order_id: number }>("/payment/confirm", {
          method: "POST",
          body: JSON.stringify({
            payment_key: paymentKey,
            pg_order_id: pgOrderId,
            amount_krw: amount,
          }),
        });
        router.replace(`/dashboard/orders/${order_id}`);
      } catch (error) {
        setState({
          phase: "error",
          message: error instanceof ApiError ? error.detail : "결제 승인에 실패했습니다.",
        });
      }
    };
    void confirm();
    // authStatus가 ready로 바뀐 뒤 1회 실행 — 가드가 재실행을 막는다
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [authStatus]);

  if (state.phase === "error") {
    return (
      <div className="mx-auto max-w-md px-4 py-20 text-center">
        <p className="text-lg font-semibold">결제를 완료하지 못했습니다</p>
        <p className="mt-2 text-sm text-muted-foreground">{state.message}</p>
        <p className="mt-1 text-xs text-muted-foreground">
          승인 전 실패는 청구되지 않으며, 승인 후 문제는 자동으로 취소 처리됩니다.
        </p>
        <Button className="mt-6" nativeButton={false} render={<Link href="/">홈으로</Link>} />
      </div>
    );
  }
  return (
    <div className="mx-auto max-w-md px-4 py-20 text-center text-muted-foreground">
      결제를 승인하고 주문을 생성하는 중입니다…
    </div>
  );
}

export default function PaySuccessPage() {
  return (
    <Suspense>
      <PaySuccessContent />
    </Suspense>
  );
}
