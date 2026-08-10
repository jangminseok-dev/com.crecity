"use client";

import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import { loadTossPayments } from "@tosspayments/tosspayments-sdk";
import { Suspense, useState } from "react";
import { z } from "zod";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Label } from "@/components/ui/label";
import { Skeleton } from "@/components/ui/skeleton";
import { Textarea } from "@/components/ui/textarea";
import { ApiError, apiFetch } from "@/lib/api";
import { useAuthStore } from "@/lib/auth-store";
import { PLATFORM_LABELS, formatKrw } from "@/lib/labels";
import type { CreatorPackage, CustomOffer } from "@/lib/types";

const orderSchema = z.object({
  requirements: z.string().min(10, "요구사항을 10자 이상 구체적으로 적어 주세요."),
});

type CheckoutResponse = {
  pg_order_id: string;
  amount_krw: number;
  order_name: string;
  client_key: string;
};

function OrderNewContent() {
  const searchParams = useSearchParams();
  const { status, user } = useAuthStore();
  const slug = searchParams.get("slug");
  const packageId = Number(searchParams.get("package"));
  // 커스텀 오퍼 결제 모드 — 채팅에서 "결제하기"로 진입
  const offerId = Number(searchParams.get("offer"));
  const conversationId = searchParams.get("conversation");
  const isOfferMode = Boolean(offerId && conversationId);
  // 단일 객체 상태 — 제출 진행·오류 (입력값은 FormData 패턴)
  const [form, setForm] = useState<{ submitting: boolean; error: string | null }>({
    submitting: false,
    error: null,
  });

  const { data: packages, isPending } = useQuery({
    queryKey: ["packages", slug],
    queryFn: () => apiFetch<CreatorPackage[]>(`/creator/profiles/${slug}/packages`),
    enabled: Boolean(slug) && !isOfferMode,
  });
  const pkg = packages?.find((p) => p.id === packageId);

  const { data: offers, isPending: offersPending } = useQuery({
    queryKey: ["offers", conversationId],
    queryFn: () => apiFetch<CustomOffer[]>(`/chat/conversations/${conversationId}/offers`),
    enabled: isOfferMode && status === "authenticated",
  });
  const offer = offers?.find((o) => o.id === offerId);

  if (!isOfferMode && (!slug || !packageId)) {
    return <p className="py-20 text-center text-muted-foreground">잘못된 접근입니다.</p>;
  }
  if (status === "guest") {
    return (
      <div className="py-20 text-center">
        <p className="text-muted-foreground">주문하려면 브랜드 계정으로 로그인해 주세요.</p>
        <Button className="mt-4" nativeButton={false} render={<Link href="/login">로그인하기</Link>} />
      </div>
    );
  }
  if (status === "authenticated" && user?.account_type !== "BRAND") {
    return (
      <p className="py-20 text-center text-muted-foreground">
        브랜드 계정만 주문할 수 있습니다 — 지금은 크리에이터 계정으로 로그인되어 있습니다.
      </p>
    );
  }
  if (status === "loading" || (isOfferMode ? offersPending : isPending)) {
    return <Skeleton className="mt-10 h-64 w-full" />;
  }
  if (isOfferMode) {
    if (!offer) {
      return <p className="py-20 text-center text-muted-foreground">오퍼를 찾을 수 없습니다.</p>;
    }
    if (offer.status !== "PENDING") {
      return <p className="py-20 text-center text-muted-foreground">이미 결제된 오퍼입니다.</p>;
    }
  } else if (!pkg) {
    return <p className="py-20 text-center text-muted-foreground">패키지를 찾을 수 없습니다.</p>;
  }

  const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    const parsed = orderSchema.safeParse(Object.fromEntries(new FormData(e.currentTarget).entries()));
    if (!parsed.success) {
      setForm({ submitting: false, error: parsed.error.issues[0].message });
      return;
    }
    setForm({ submitting: true, error: null });
    try {
      // 1) 결제 준비 — 서버가 금액을 확정하고 결제창 파라미터를 내려준다
      const checkout = isOfferMode
        ? await apiFetch<CheckoutResponse>("/payment/checkouts/offer", {
            method: "POST",
            body: JSON.stringify({ offer_id: offerId, requirements: parsed.data.requirements }),
          })
        : await apiFetch<CheckoutResponse>("/payment/checkouts", {
            method: "POST",
            body: JSON.stringify({ package_id: pkg!.id, requirements: parsed.data.requirements }),
          });
      if (!checkout.client_key) {
        setForm({ submitting: false, error: "결제 설정이 아직 완료되지 않았습니다(토스 키 미설정)." });
        return;
      }
      // 2) 토스 결제창(SDK v2) — 성공 시 successUrl로 리다이렉트되어 승인 단계로 이어진다
      const tossPayments = await loadTossPayments(checkout.client_key);
      const payment = tossPayments.payment({ customerKey: `crecity-user-${user!.id}` });
      await payment.requestPayment({
        method: "CARD",
        amount: { currency: "KRW", value: checkout.amount_krw },
        orderId: checkout.pg_order_id,
        orderName: checkout.order_name,
        successUrl: `${window.location.origin}/orders/pay/success`,
        failUrl: `${window.location.origin}/orders/pay/fail`,
      });
    } catch (error) {
      setForm({
        submitting: false,
        error:
          error instanceof ApiError
            ? error.detail
            : error instanceof Error && error.message
              ? error.message // 결제창 닫힘 등 SDK 오류
              : "결제 시작에 실패했습니다.",
      });
    }
  };

  return (
    <div>
      <h1 className="text-2xl font-bold">주문서 작성</h1>
      <Card className="mt-6">
        <CardContent className="flex items-center justify-between gap-4 p-4">
          {isOfferMode ? (
            <>
              <div className="flex items-center gap-2">
                <Badge variant="outline">커스텀 오퍼</Badge>
                <p className="font-medium">{offer!.title}</p>
              </div>
              <p className="shrink-0 text-lg font-bold">{formatKrw(offer!.price_krw)}</p>
            </>
          ) : (
            <>
              <div>
                <div className="flex items-center gap-2">
                  <Badge variant="outline">{PLATFORM_LABELS[pkg!.platform]}</Badge>
                  <p className="font-medium">{pkg!.title}</p>
                </div>
                <p className="mt-1 text-sm text-muted-foreground">{pkg!.description}</p>
              </div>
              <p className="shrink-0 text-lg font-bold">{formatKrw(pkg!.price_krw)}</p>
            </>
          )}
        </CardContent>
      </Card>

      <form onSubmit={handleSubmit} className="mt-6 grid gap-4">
        <div className="grid gap-1.5">
          <Label htmlFor="requirements">요구사항</Label>
          <Textarea
            id="requirements"
            name="requirements"
            rows={6}
            placeholder="원하는 콘텐츠 방향·필수 포함 내용·게시 희망일 등을 구체적으로 적어 주세요. 수정 요청은 이 요구사항 범위 안에서 가능합니다."
          />
        </div>
        <p className="rounded-md bg-muted p-3 text-sm text-muted-foreground">
          결제하면 플랫폼 수수료가 더해진 총액이 안전거래(에스크로)로 보관되며, 콘텐츠 승인 후
          크리에이터에게 정산됩니다. 크리에이터가 72시간 내 수락하지 않으면 자동 환불됩니다.
        </p>
        {form.error && <p className="text-sm text-destructive">{form.error}</p>}
        <Button type="submit" size="lg" disabled={form.submitting}>
          {form.submitting ? "결제창 여는 중…" : "결제하고 주문하기"}
        </Button>
      </form>
    </div>
  );
}

export default function OrderNewPage() {
  return (
    <div className="mx-auto max-w-2xl px-4 py-10">
      <Suspense>
        <OrderNewContent />
      </Suspense>
    </div>
  );
}
