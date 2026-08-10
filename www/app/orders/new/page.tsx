"use client";

import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
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
import type { CreatorPackage, Order } from "@/lib/types";

const orderSchema = z.object({
  requirements: z.string().min(10, "요구사항을 10자 이상 구체적으로 적어 주세요."),
});

function OrderNewContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { status, user } = useAuthStore();
  const slug = searchParams.get("slug");
  const packageId = Number(searchParams.get("package"));
  // 단일 객체 상태 — 제출 진행·오류 (입력값은 FormData 패턴)
  const [form, setForm] = useState<{ submitting: boolean; error: string | null }>({
    submitting: false,
    error: null,
  });

  const { data: packages, isPending } = useQuery({
    queryKey: ["packages", slug],
    queryFn: () => apiFetch<CreatorPackage[]>(`/creator/profiles/${slug}/packages`),
    enabled: Boolean(slug),
  });
  const pkg = packages?.find((p) => p.id === packageId);

  if (!slug || !packageId) {
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
  if (status === "loading" || isPending) return <Skeleton className="mt-10 h-64 w-full" />;
  if (!pkg) {
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
      const order = await apiFetch<Order>("/order/orders", {
        method: "POST",
        body: JSON.stringify({ package_id: pkg.id, requirements: parsed.data.requirements }),
      });
      router.replace(`/dashboard/orders/${order.id}`);
    } catch (error) {
      setForm({
        submitting: false,
        error: error instanceof ApiError ? error.detail : "주문에 실패했습니다.",
      });
    }
  };

  return (
    <div>
      <h1 className="text-2xl font-bold">주문서 작성</h1>
      <Card className="mt-6">
        <CardContent className="flex items-center justify-between gap-4 p-4">
          <div>
            <div className="flex items-center gap-2">
              <Badge variant="outline">{PLATFORM_LABELS[pkg.platform]}</Badge>
              <p className="font-medium">{pkg.title}</p>
            </div>
            <p className="mt-1 text-sm text-muted-foreground">{pkg.description}</p>
          </div>
          <p className="shrink-0 text-lg font-bold">{formatKrw(pkg.price_krw)}</p>
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
          주문 확정 시 플랫폼 수수료가 더해진 결제 총액이 안전거래(에스크로)로 보관되며, 콘텐츠
          승인 후 크리에이터에게 정산됩니다. 크리에이터가 72시간 내 수락하지 않으면 자동
          환불됩니다. (실제 카드 결제는 연동 준비 중 — 지금은 주문 기록만 생성됩니다)
        </p>
        {form.error && <p className="text-sm text-destructive">{form.error}</p>}
        <Button type="submit" size="lg" disabled={form.submitting}>
          {form.submitting ? "주문 생성 중…" : "주문하기"}
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
