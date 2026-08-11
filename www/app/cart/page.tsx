"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import { loadTossPayments } from "@tosspayments/tosspayments-sdk";
import { useEffect, useState } from "react";
import { z } from "zod";

import { ShieldCheck, Trash2 } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { ApiError, apiFetch } from "@/lib/api";
import { useAuthStore } from "@/lib/auth-store";
import { useCartStore } from "@/lib/cart-store";
import { PLATFORM_LABELS, formatKrw } from "@/lib/labels";
import type { Balance } from "@/lib/types";

const cartSchema = z.object({
  requirements: z.string().min(10, "요구사항을 10자 이상 구체적으로 적어 주세요."),
});

type CheckoutResponse = {
  pg_order_id: string;
  amount_krw: number;
  credit_applied_krw: number;
  pg_amount_krw: number;
  order_name: string;
  client_key: string;
};

export default function CartPage() {
  const router = useRouter();
  const { status, user } = useAuthStore();
  const cart = useCartStore();
  // 단일 객체 상태 — 하이드레이션·제출 진행·오류 (입력값은 FormData 패턴)
  const [ui, setUi] = useState<{ ready: boolean; submitting: boolean; error: string | null }>({
    ready: false,
    submitting: false,
    error: null,
  });
  useEffect(() => setUi((prev) => ({ ...prev, ready: true })), []);

  const { data: balance } = useQuery({
    queryKey: ["balance"],
    queryFn: () => apiFetch<Balance>("/order/balance"),
    enabled: status === "authenticated" && user?.account_type === "BRAND",
  });
  const creditKrw = balance?.balance_krw ?? 0;

  if (!ui.ready) return null;

  if (cart.items.length === 0) {
    return (
      <div className="mx-auto max-w-[560px] px-4 py-20 text-center">
        <p className="text-muted-foreground">장바구니가 비어 있습니다.</p>
        <Button className="mt-4" nativeButton={false} render={<Link href="/">크리에이터 찾기</Link>} />
      </div>
    );
  }

  const priceSum = cart.items.reduce((sum, item) => sum + item.price_krw, 0);

  const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    const formData = new FormData(e.currentTarget);
    const parsed = cartSchema.safeParse(Object.fromEntries(formData.entries()));
    if (!parsed.success) {
      setUi((prev) => ({ ...prev, error: parsed.error.issues[0].message }));
      return;
    }
    const useCredit = formData.get("use_credit") === "on";
    setUi((prev) => ({ ...prev, submitting: true, error: null }));
    try {
      // 1) 결제 준비 — 서버가 항목별 가격을 재확정하고 총액·크레딧 적용액을 내려준다
      const checkout = await apiFetch<CheckoutResponse>("/payment/checkouts/cart", {
        method: "POST",
        body: JSON.stringify({
          package_ids: cart.items.map((item) => item.package_id),
          requirements: parsed.data.requirements,
          use_credit: useCredit,
        }),
      });
      // 2) 전액 크레딧이면 결제창 없이 바로 승인 — 주문 N건 생성으로 직행
      if (checkout.pg_amount_krw === 0) {
        const { order_ids } = await apiFetch<{ order_id: number; order_ids: number[] }>(
          "/payment/confirm",
          {
            method: "POST",
            body: JSON.stringify({
              payment_key: "",
              pg_order_id: checkout.pg_order_id,
              amount_krw: 0,
            }),
          },
        );
        cart.clear();
        router.replace(order_ids.length > 1 ? "/dashboard/orders" : `/dashboard/orders/${order_ids[0]}`);
        return;
      }
      if (!checkout.client_key) {
        setUi((prev) => ({
          ...prev,
          submitting: false,
          error: "결제 설정이 아직 완료되지 않았습니다(토스 키 미설정).",
        }));
        return;
      }
      // 3) 토스 결제창 — 성공 시 successUrl에서 승인·카트 비우기가 이어진다
      const tossPayments = await loadTossPayments(checkout.client_key);
      const payment = tossPayments.payment({ customerKey: `crecity-user-${user!.id}` });
      await payment.requestPayment({
        method: "CARD",
        amount: { currency: "KRW", value: checkout.pg_amount_krw },
        orderId: checkout.pg_order_id,
        orderName: checkout.order_name,
        successUrl: `${window.location.origin}/orders/pay/success`,
        failUrl: `${window.location.origin}/orders/pay/fail`,
      });
    } catch (error) {
      setUi((prev) => ({
        ...prev,
        submitting: false,
        error:
          error instanceof ApiError
            ? error.detail
            : error instanceof Error && error.message
              ? error.message
              : "결제 시작에 실패했습니다.",
      }));
    }
  };

  return (
    <div className="mx-auto max-w-[560px] px-4 py-12">
      <h1 className="text-[26px] font-bold tracking-[-0.02em]">장바구니</h1>
      <p className="mt-1 text-sm text-muted-foreground">
        여러 크리에이터의 패키지를 한 번에 결제하면 크리에이터별 주문이 각각 생성됩니다.
      </p>

      <section className="mt-6 grid gap-2.5">
        {cart.items.map((item) => (
          <div key={item.package_id} className="flex items-center gap-3 rounded-2xl border p-4">
            <div className="min-w-0 flex-1">
              <Badge variant="outline">{PLATFORM_LABELS[item.platform]}</Badge>
              <p className="mt-1.5 truncate text-[15px] font-semibold">{item.title}</p>
              <Link
                href={`/creators/${item.creator_slug}`}
                className="text-[13px] text-muted-foreground underline-offset-2 hover:underline"
              >
                프로필 보기 ↗
              </Link>
            </div>
            <p className="shrink-0 font-bold">{formatKrw(item.price_krw)}</p>
            <button
              type="button"
              aria-label="장바구니에서 빼기"
              onClick={() => cart.remove(item.package_id)}
              className="inline-flex size-9 shrink-0 items-center justify-center rounded-full text-muted-foreground transition-colors hover:bg-secondary hover:text-destructive"
            >
              <Trash2 className="size-4" />
            </button>
          </div>
        ))}
      </section>

      <p className="mt-3 flex items-baseline justify-between rounded-xl bg-muted px-4 py-3 text-sm">
        <span className="text-muted-foreground">
          패키지 합계 ({cart.items.length}건) — 플랫폼 수수료는 결제 시 더해집니다
        </span>
        <span className="text-base font-bold">{formatKrw(priceSum)}</span>
      </p>

      {status === "guest" ? (
        <div className="mt-6 text-center">
          <p className="text-sm text-muted-foreground">결제하려면 브랜드 계정으로 로그인해 주세요.</p>
          <Button className="mt-3" nativeButton={false} render={<Link href="/login">로그인하기</Link>} />
        </div>
      ) : user?.account_type !== "BRAND" ? (
        <p className="mt-6 text-center text-sm text-muted-foreground">
          브랜드 계정만 결제할 수 있습니다.
        </p>
      ) : (
        <form onSubmit={handleSubmit} className="mt-5 grid gap-4">
          <div className="grid gap-1.5">
            <Label htmlFor="requirements">공통 요구사항</Label>
            <Textarea
              id="requirements"
              name="requirements"
              rows={5}
              placeholder="모든 주문에 동일하게 적용될 브리프를 적어 주세요. 크리에이터별 세부 조율은 주문 후 채팅으로 가능합니다."
            />
          </div>
          {creditKrw > 0 && (
            <label className="flex items-center gap-2.5 rounded-xl border px-3.5 py-3 text-sm">
              <input type="checkbox" name="use_credit" className="size-4 accent-primary" />
              <span>
                보유 크레딧 사용 <span className="font-semibold">{formatKrw(creditKrw)}</span>
              </span>
            </label>
          )}
          <div className="flex items-start gap-2 rounded-xl bg-[#f9fafb] px-3.5 py-3 text-[13px] leading-snug text-muted-foreground">
            <ShieldCheck className="mt-0.5 size-[18px] shrink-0 text-primary" />
            결제하면 크리에이터별 주문이 각각 생성되고, 수수료 포함 총액이 안전거래(에스크로)로
            보관됩니다. 각 주문은 개별로 수락·거절될 수 있으며 거절분은 크레딧으로 환불됩니다.
          </div>
          {ui.error && <p className="text-sm text-destructive">{ui.error}</p>}
          <button
            type="submit"
            disabled={ui.submitting}
            className="inline-flex h-[52px] w-full items-center justify-center rounded-xl bg-primary text-[17px] font-semibold text-primary-foreground transition-colors hover:bg-accent-foreground disabled:bg-muted disabled:text-muted-foreground"
          >
            {ui.submitting ? "결제창 여는 중…" : `${cart.items.length}건 한 번에 결제하기`}
          </button>
        </form>
      )}
    </div>
  );
}
