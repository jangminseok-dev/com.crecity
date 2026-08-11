"use client";

import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import { loadTossPayments } from "@tosspayments/tosspayments-sdk";
import { Suspense, useState } from "react";
import { z } from "zod";

import { ShieldCheck } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { Skeleton } from "@/components/ui/skeleton";
import { Textarea } from "@/components/ui/textarea";
import { ApiError, apiFetch } from "@/lib/api";
import { useAuthStore } from "@/lib/auth-store";
import { PLATFORM_LABELS, formatKrw } from "@/lib/labels";
import type { Balance, CampaignApplication, CreatorPackage, CustomOffer } from "@/lib/types";

const orderSchema = z.object({
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

function OrderNewContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { status, user } = useAuthStore();
  const slug = searchParams.get("slug");
  const packageId = Number(searchParams.get("package"));
  // 커스텀 오퍼 결제 모드 — 채팅에서 "결제하기"로 진입
  const offerId = Number(searchParams.get("offer"));
  const conversationId = searchParams.get("conversation");
  const isOfferMode = Boolean(offerId && conversationId);
  // 캠페인 지원 수락 모드 — 지원자 목록에서 "수락하고 결제"로 진입
  const applicationId = Number(searchParams.get("application"));
  const applicationCampaignId = searchParams.get("campaign");
  const isApplicationMode = Boolean(applicationId && applicationCampaignId);
  // 단일 객체 상태 — 제출 진행·오류 (입력값은 FormData 패턴)
  const [form, setForm] = useState<{ submitting: boolean; error: string | null }>({
    submitting: false,
    error: null,
  });

  const { data: packages, isPending } = useQuery({
    queryKey: ["packages", slug],
    queryFn: () => apiFetch<CreatorPackage[]>(`/creator/profiles/${slug}/packages`),
    enabled: Boolean(slug) && !isOfferMode && !isApplicationMode,
  });
  const pkg = packages?.find((p) => p.id === packageId);

  const { data: applications, isPending: applicationsPending } = useQuery({
    queryKey: ["campaignApplications", applicationCampaignId],
    queryFn: () =>
      apiFetch<CampaignApplication[]>(
        `/campaign/campaigns/${applicationCampaignId}/applications`,
      ),
    enabled: isApplicationMode && status === "authenticated",
  });
  const application = applications?.find((a) => a.id === applicationId);

  const { data: offers, isPending: offersPending } = useQuery({
    queryKey: ["offers", conversationId],
    queryFn: () => apiFetch<CustomOffer[]>(`/chat/conversations/${conversationId}/offers`),
    enabled: isOfferMode && status === "authenticated",
  });
  const offer = offers?.find((o) => o.id === offerId);

  // 보유 크레딧(환불 적립 등) — 있으면 결제에 사용할 수 있다
  const { data: balance } = useQuery({
    queryKey: ["balance"],
    queryFn: () => apiFetch<Balance>("/order/balance"),
    enabled: status === "authenticated" && user?.account_type === "BRAND",
  });
  const creditKrw = balance?.balance_krw ?? 0;

  if (!isOfferMode && !isApplicationMode && (!slug || !packageId)) {
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
  if (
    status === "loading" ||
    (isApplicationMode ? applicationsPending : isOfferMode ? offersPending : isPending)
  ) {
    return <Skeleton className="mt-10 h-64 w-full" />;
  }
  if (isApplicationMode) {
    if (!application) {
      return <p className="py-20 text-center text-muted-foreground">지원을 찾을 수 없습니다.</p>;
    }
    if (application.order_id) {
      return <p className="py-20 text-center text-muted-foreground">이미 수락된 지원입니다.</p>;
    }
  } else if (isOfferMode) {
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
    const formData = new FormData(e.currentTarget);
    const parsed = orderSchema.safeParse(Object.fromEntries(formData.entries()));
    if (!parsed.success) {
      setForm({ submitting: false, error: parsed.error.issues[0].message });
      return;
    }
    const useCredit = formData.get("use_credit") === "on";
    setForm({ submitting: true, error: null });
    try {
      // 1) 결제 준비 — 서버가 금액·크레딧 적용액을 확정하고 결제창 파라미터를 내려준다
      const checkout = isApplicationMode
        ? await apiFetch<CheckoutResponse>("/payment/checkouts/application", {
            method: "POST",
            body: JSON.stringify({
              application_id: applicationId,
              requirements: parsed.data.requirements,
              use_credit: useCredit,
            }),
          })
        : isOfferMode
          ? await apiFetch<CheckoutResponse>("/payment/checkouts/offer", {
              method: "POST",
              body: JSON.stringify({
                offer_id: offerId,
                requirements: parsed.data.requirements,
                use_credit: useCredit,
              }),
            })
          : await apiFetch<CheckoutResponse>("/payment/checkouts", {
              method: "POST",
              body: JSON.stringify({
                package_id: pkg!.id,
                requirements: parsed.data.requirements,
                use_credit: useCredit,
              }),
            });
      // 2) 전액 크레딧(PG 결제액 0)이면 결제창 없이 바로 승인 — 주문 생성으로 직행
      if (checkout.pg_amount_krw === 0) {
        const { order_id } = await apiFetch<{ order_id: number }>("/payment/confirm", {
          method: "POST",
          body: JSON.stringify({
            payment_key: "",
            pg_order_id: checkout.pg_order_id,
            amount_krw: 0,
          }),
        });
        router.replace(`/dashboard/orders/${order_id}`);
        return;
      }
      if (!checkout.client_key) {
        setForm({ submitting: false, error: "결제 설정이 아직 완료되지 않았습니다(토스 키 미설정)." });
        return;
      }
      // 3) 토스 결제창(SDK v2) — 성공 시 successUrl로 리다이렉트되어 승인 단계로 이어진다
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
      <h1 className="text-[26px] font-bold tracking-[-0.02em]">주문·결제</h1>

      <section className="mt-7 rounded-2xl border p-5">
        {isApplicationMode ? (
          <div className="flex items-center justify-between gap-4">
            <div className="min-w-0">
              <Badge variant="outline">캠페인 지원 수락</Badge>
              <p className="mt-2 text-[15px] font-semibold">{application!.creator_name}</p>
              <p className="mt-1 text-[13px] leading-snug text-muted-foreground">
                {application!.message}
              </p>
            </div>
            <p className="shrink-0 text-lg font-bold">
              {formatKrw(application!.proposed_price_krw)}
            </p>
          </div>
        ) : isOfferMode ? (
          <div className="flex items-center justify-between gap-4">
            <div className="min-w-0">
              <Badge variant="outline">커스텀 오퍼</Badge>
              <p className="mt-2 text-[15px] font-semibold">{offer!.title}</p>
            </div>
            <p className="shrink-0 text-lg font-bold">{formatKrw(offer!.price_krw)}</p>
          </div>
        ) : (
          <div className="flex items-start justify-between gap-4">
            <div className="min-w-0">
              <Badge variant="outline">{PLATFORM_LABELS[pkg!.platform]}</Badge>
              <p className="mt-2 text-[15px] font-semibold">{pkg!.title}</p>
              <p className="mt-1 text-[13px] leading-snug text-muted-foreground">
                {pkg!.description}
              </p>
            </div>
            <p className="shrink-0 text-lg font-bold">{formatKrw(pkg!.price_krw)}</p>
          </div>
        )}
      </section>

      <form onSubmit={handleSubmit} className="mt-4 grid gap-4">
        <div className="grid gap-1.5">
          <Label htmlFor="requirements">요구사항</Label>
          <Textarea
            id="requirements"
            name="requirements"
            rows={6}
            placeholder="원하는 콘텐츠 방향·필수 포함 내용·게시 희망일 등을 구체적으로 적어 주세요. 수정 요청은 이 요구사항 범위 안에서 가능합니다."
          />
        </div>
        {creditKrw > 0 && (
          <label className="flex items-center gap-2.5 rounded-xl border px-3.5 py-3 text-sm">
            <input type="checkbox" name="use_credit" className="size-4 accent-primary" />
            <span>
              보유 크레딧 사용 <span className="font-semibold">{formatKrw(creditKrw)}</span>
              <span className="ml-1 text-[13px] text-muted-foreground">
                — 결제 금액에서 자동 차감됩니다
              </span>
            </span>
          </label>
        )}
        <div className="flex items-start gap-2 rounded-xl bg-[#f9fafb] px-3.5 py-3 text-[13px] leading-snug text-muted-foreground">
          <ShieldCheck className="mt-0.5 size-[18px] shrink-0 text-primary" />
          결제하면 플랫폼 수수료가 더해진 총액이 안전거래(에스크로)로 보관되며, 콘텐츠 승인 후
          크리에이터에게 정산됩니다. 크리에이터가 72시간 내 수락하지 않으면 자동 환불됩니다.
        </div>
        {form.error && <p className="text-sm text-destructive">{form.error}</p>}
        <button
          type="submit"
          disabled={form.submitting}
          className="inline-flex h-[52px] w-full items-center justify-center rounded-xl bg-primary text-[17px] font-semibold text-primary-foreground transition-colors hover:bg-accent-foreground disabled:bg-muted disabled:text-muted-foreground"
        >
          {form.submitting ? "결제창 여는 중…" : "결제하고 주문하기"}
        </button>
      </form>
    </div>
  );
}

export default function OrderNewPage() {
  return (
    <div className="mx-auto max-w-[520px] px-4 py-12">
      <Suspense>
        <OrderNewContent />
      </Suspense>
    </div>
  );
}
