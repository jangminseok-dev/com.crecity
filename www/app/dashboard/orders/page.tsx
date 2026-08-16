"use client";

import { ChevronRight } from "lucide-react";
import Link from "next/link";
import { useState } from "react";
import { useQuery } from "@tanstack/react-query";

import BrandOnboarding from "@/components/brand-onboarding";
import OrderStatusBadge from "@/components/order-status-badge";
import { Skeleton } from "@/components/ui/skeleton";
import { apiFetch } from "@/lib/api";
import { useAuthStore } from "@/lib/auth-store";
import { formatDeadline, formatKrw } from "@/lib/labels";
import type { Order } from "@/lib/types";

/* 상태 필터 탭 — 디자인 시스템 OrdersScreen */
const TABS: { id: string; label: string; statuses: Order["status"][] | null }[] = [
  { id: "all", label: "전체", statuses: null },
  { id: "active", label: "진행중", statuses: ["PENDING_ACCEPT", "IN_PROGRESS"] },
  { id: "review", label: "검토 대기", statuses: ["IN_REVIEW"] },
  { id: "done", label: "완료", statuses: ["COMPLETED"] },
  { id: "cancel", label: "취소·환불", statuses: ["REFUNDED", "CANCELLED"] },
];

export default function DashboardOrdersPage() {
  const user = useAuthStore((s) => s.user);
  const [tab, setTab] = useState("all");
  const { data: orders, isPending } = useQuery({
    queryKey: ["myOrders"],
    queryFn: () => apiFetch<Order[]>("/order/orders"),
  });

  if (isPending || !user) return <Skeleton className="h-64 w-full" />;
  if (!orders || orders.length === 0) {
    // 브랜드는 가입 직후 할 일이 안 보인다(갭 #78) — 빈 목록 자리에 첫 걸음을 안내한다
    if (user.account_type === "BRAND") return <BrandOnboarding />;
    return (
      <p className="rounded-xl border border-dashed py-16 text-center text-muted-foreground">
        아직 주문이 없습니다.
      </p>
    );
  }

  const activeTab = TABS.find((t) => t.id === tab) ?? TABS[0];
  const list = activeTab.statuses
    ? orders.filter((order) => activeTab.statuses!.includes(order.status))
    : orders;
  const countOf = (statuses: Order["status"][] | null) =>
    statuses ? orders.filter((o) => statuses.includes(o.status)).length : orders.length;

  return (
    <div>
      <div className="flex gap-0.5 overflow-x-auto border-b">
        {TABS.map((t) => (
          <button
            key={t.id}
            type="button"
            onClick={() => setTab(t.id)}
            className={
              tab === t.id
                ? "-mb-px whitespace-nowrap border-b-2 border-foreground px-3.5 py-2.5 text-sm font-semibold"
                : "whitespace-nowrap px-3.5 py-2.5 text-sm text-muted-foreground transition-colors hover:text-foreground"
            }
          >
            {t.label}
            <span className={`ml-1 text-xs ${tab === t.id ? "text-muted-foreground" : "text-muted-foreground/60"}`}>
              {countOf(t.statuses)}
            </span>
          </button>
        ))}
      </div>

      {list.length === 0 ? (
        <p className="py-12 text-center text-sm text-muted-foreground/70">
          해당 상태의 주문이 없어요
        </p>
      ) : (
        <div>
          {list.map((order) => {
            const isBrand = order.brand_user_id === user.id;
            return (
              <Link
                key={order.id}
                href={`/dashboard/orders/${order.id}`}
                className="flex items-center gap-4 border-b px-1 py-4.5 transition-colors hover:bg-muted/40"
              >
                <div className="min-w-0 flex-1">
                  <p className="truncate text-[15px] font-semibold">{order.package_title}</p>
                  <p className="mt-0.5 truncate text-[13px] text-muted-foreground">
                    주문 #{order.id} · {isBrand ? "내가 주문함" : "받은 주문"}
                    {order.deadline_at && ` · ${formatDeadline(order.deadline_at)}`}
                  </p>
                </div>
                <p className="shrink-0 text-[15px] font-bold">
                  {formatKrw(isBrand ? order.brand_total_krw : order.creator_payout_krw)}
                </p>
                <OrderStatusBadge status={order.status} />
                <ChevronRight className="size-4.5 shrink-0 text-muted-foreground/50" />
              </Link>
            );
          })}
        </div>
      )}
    </div>
  );
}
