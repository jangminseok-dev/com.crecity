"use client";

import { useQuery } from "@tanstack/react-query";

import { Card, CardContent } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { apiFetch } from "@/lib/api";
import { formatKrw } from "@/lib/labels";

type DashboardMetrics = {
  total_users: number;
  creator_users: number;
  brand_users: number;
  pending_review: number;
  approved_profiles: number;
  rejected_profiles: number;
  pending_accept: number;
  in_progress: number;
  in_review: number;
  completed: number;
  refunded: number;
  cancelled: number;
  gmv_krw: number;
  platform_revenue_krw: number;
  open_disputes: number;
  pending_withdrawals: number;
  pending_withdrawal_krw: number;
};

function Tile({
  label,
  value,
  hint,
  alert = false,
}: {
  label: string;
  value: string;
  hint?: string;
  alert?: boolean;
}) {
  return (
    <div className="rounded-xl border bg-card p-4">
      <p className="text-[13px] text-muted-foreground">{label}</p>
      <p
        className={`mt-1 text-[22px] font-bold tracking-[-0.02em] ${
          alert ? "text-destructive" : ""
        }`}
      >
        {value}
      </p>
      {hint && <p className="mt-0.5 text-xs text-muted-foreground">{hint}</p>}
    </div>
  );
}

/** 운영 대시보드 지표(갭 #55) — dashboard.view 권한. 조회 시점 집계라 저장하지 않는다. */
export default function AdminDashboardMetrics() {
  const { data, isPending } = useQuery({
    queryKey: ["dashboardMetrics"],
    queryFn: () => apiFetch<DashboardMetrics>("/admin/dashboard/metrics"),
  });

  if (isPending) {
    return (
      <section className="mb-10">
        <h2 className="text-xl font-bold tracking-[-0.02em]">운영 현황</h2>
        <div className="mt-4 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
          {[0, 1, 2, 3].map((key) => (
            <Skeleton key={key} className="h-[92px] rounded-xl" />
          ))}
        </div>
      </section>
    );
  }
  if (!data) return null;

  const activeOrders = data.pending_accept + data.in_progress + data.in_review;

  return (
    <section className="mb-10">
      <h2 className="text-xl font-bold tracking-[-0.02em]">운영 현황</h2>

      {/* 처리해야 할 일 — 0이 아니면 눈에 띄어야 한다 */}
      <div className="mt-4 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
        <Tile
          label="심사 대기"
          value={`${data.pending_review}건`}
          alert={data.pending_review > 0}
        />
        <Tile
          label="분쟁 대기"
          value={`${data.open_disputes}건`}
          alert={data.open_disputes > 0}
        />
        <Tile
          label="인출 대기"
          value={`${data.pending_withdrawals}건`}
          hint={
            data.pending_withdrawals > 0
              ? `이체할 금액 ${formatKrw(data.pending_withdrawal_krw)}`
              : undefined
          }
          alert={data.pending_withdrawals > 0}
        />
        <Tile label="진행 중 주문" value={`${activeOrders}건`} />
      </div>

      {/* 누적 지표 */}
      <div className="mt-3 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
        <Tile
          label="거래액(완료 주문)"
          value={formatKrw(data.gmv_krw)}
          hint={`완료 ${data.completed}건`}
        />
        <Tile
          label="수수료 수입"
          value={formatKrw(data.platform_revenue_krw)}
          hint="원장 기준"
        />
        <Tile
          label="가입"
          value={`${data.total_users}명`}
          hint={`크리에이터 ${data.creator_users} · 브랜드 ${data.brand_users}`}
        />
        <Tile
          label="공개 프로필"
          value={`${data.approved_profiles}명`}
          hint={`반려 ${data.rejected_profiles}`}
        />
      </div>

      {/* 주문 상태 분포 */}
      <Card className="mt-3">
        <CardContent className="flex flex-wrap gap-x-6 gap-y-2 p-4 text-sm">
          {[
            { label: "수락 대기", value: data.pending_accept },
            { label: "작업 중", value: data.in_progress },
            { label: "검토 대기", value: data.in_review },
            { label: "완료", value: data.completed },
            { label: "환불", value: data.refunded },
            { label: "취소", value: data.cancelled },
          ].map((item) => (
            <span key={item.label} className="text-muted-foreground">
              {item.label} <span className="font-semibold text-foreground">{item.value}</span>
            </span>
          ))}
        </CardContent>
      </Card>
    </section>
  );
}
