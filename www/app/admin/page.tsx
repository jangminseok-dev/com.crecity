"use client";

import { useQuery } from "@tanstack/react-query";
import { usePathname, useRouter, useSearchParams } from "next/navigation";
import { Suspense } from "react";

import AdminAnnualPayouts from "@/components/admin-annual-payouts";
import AdminAuditLogs from "@/components/admin-audit-logs";
import AdminDashboardMetrics from "@/components/admin-dashboard-metrics";
import AdminDisputes from "@/components/admin-disputes";
import AdminFlaggedAnalytics from "@/components/admin-flagged-analytics";
import AdminOrderSearch from "@/components/admin-order-search";
import AdminPendingProfiles from "@/components/admin-pending-profiles";
import AdminReports from "@/components/admin-reports";
import AdminWithdrawals from "@/components/admin-withdrawals";
import { Skeleton } from "@/components/ui/skeleton";
import { apiFetch } from "@/lib/api";
import { useAuthStore } from "@/lib/auth-store";
import { cn } from "@/lib/utils";

/** 왼쪽 탭 목록 — 권한이 없는 탭은 목록에서 빠진다. 순서가 곧 화면 순서. */
const TABS = [
  { key: "dashboard", label: "운영 현황", permission: "dashboard.view", Section: AdminDashboardMetrics },
  { key: "profiles", label: "프로필 심사", permission: "profile.review", Section: AdminPendingProfiles },
  { key: "withdrawals", label: "인출 처리", permission: "withdrawal.settle", Section: AdminWithdrawals },
  { key: "annual", label: "연간 지급 집계", permission: "withdrawal.settle", Section: AdminAnnualPayouts },
  { key: "flagged", label: "지표 재검토", permission: "profile.review", Section: AdminFlaggedAnalytics },
  { key: "disputes", label: "분쟁 중재", permission: "dispute.resolve", Section: AdminDisputes },
  { key: "reports", label: "신고 처리", permission: "report.review", Section: AdminReports },
  { key: "orders", label: "주문 검색", permission: "order.search", Section: AdminOrderSearch },
  { key: "audit", label: "감사 로그", permission: null, Section: AdminAuditLogs },
] as const;

/** 탭 옆 대기 건수 — 각 섹션과 같은 캐시 키를 써서 승인·처리 직후 섹션이 무효화하면 배지도 같이 줄어든다. */
function useQueueCounts(has: (permission: string) => boolean): Partial<Record<string, number>> {
  const useQueueLength = (key: readonly unknown[], path: string, permission: string) =>
    useQuery({
      queryKey: key,
      queryFn: () => apiFetch<unknown[]>(path),
      enabled: has(permission),
      select: (items) => items.length,
    }).data;
  return {
    profiles: useQueueLength(["pendingProfiles"], "/admin/profiles/pending", "profile.review"),
    withdrawals: useQueueLength(["pendingWithdrawals"], "/admin/withdrawals/pending", "withdrawal.settle"),
    disputes: useQueueLength(["disputes", false], "/admin/disputes/open", "dispute.resolve"),
    reports: useQueueLength(["reports", false], "/admin/reports/open", "report.review"),
  };
}

function AdminConsole() {
  const { user } = useAuthStore();
  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();

  const has = (permission: string) => user?.permissions.includes(permission) ?? false;
  const tabs = TABS.filter((tab) => tab.permission === null || has(tab.permission));
  const counts = useQueueCounts(has);
  // 탭은 URL(?tab=)에 둔다 — 새로고침·뒤로가기에도 자리가 유지된다
  const requested = searchParams.get("tab");
  const active = tabs.find((tab) => tab.key === requested) ?? tabs[0];

  return (
    <div className="grid gap-6 md:grid-cols-[180px_1fr] md:gap-10">
      <nav aria-label="운영 메뉴" className="-mx-4 overflow-x-auto px-4 md:mx-0 md:px-0">
        <ul className="flex gap-1 md:flex-col">
          {tabs.map((tab) => (
            <li key={tab.key} className="shrink-0">
              <button
                type="button"
                aria-current={tab.key === active.key ? "page" : undefined}
                onClick={() => router.replace(`${pathname}?tab=${tab.key}`)}
                className={cn(
                  "flex w-full items-center gap-2 whitespace-nowrap rounded-lg px-3 py-2 text-left text-sm transition-colors",
                  tab.key === active.key
                    ? "bg-muted font-semibold"
                    : "text-muted-foreground hover:bg-muted/60 hover:text-foreground",
                )}
              >
                {tab.label}
                {(counts[tab.key] ?? 0) > 0 && (
                  <span className="ml-auto rounded-full bg-destructive px-1.5 text-[11px] font-semibold leading-[18px] text-white">
                    {counts[tab.key]}
                  </span>
                )}
              </button>
            </li>
          ))}
        </ul>
      </nav>

      {/* 섹션 컴포넌트는 세로 나열 시절의 mt-12/mb-10을 아직 갖고 있다 — 단독 표시라 상쇄 */}
      <div className="min-w-0 [&>section]:mt-0 [&>section]:mb-0">
        <active.Section />
      </div>
    </div>
  );
}

export default function AdminPage() {
  const { status, user } = useAuthStore();
  const canReview = user?.permissions.includes("profile.review") ?? false;

  if (status === "loading") {
    return (
      <div className="mx-auto max-w-5xl px-4 py-10">
        <Skeleton className="h-64 w-full" />
      </div>
    );
  }
  if (!canReview) {
    return (
      <p className="mx-auto max-w-3xl px-4 py-20 text-center text-muted-foreground">
        운영자 권한(profile.review)이 있는 계정만 접근할 수 있습니다.
      </p>
    );
  }

  return (
    <div className="mx-auto max-w-5xl px-4 py-10">
      <h1 className="mb-8 text-2xl font-bold tracking-[-0.02em]">운영 콘솔</h1>
      <Suspense>
        <AdminConsole />
      </Suspense>
    </div>
  );
}
