"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useEffect } from "react";

import { Skeleton } from "@/components/ui/skeleton";
import { useAuthStore } from "@/lib/auth-store";

const TABS = [
  { href: "/dashboard/profile", label: "내 프로필" },
  { href: "/dashboard/packages", label: "판매 패키지" },
];

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  const { status, user } = useAuthStore();
  const router = useRouter();
  const pathname = usePathname();

  useEffect(() => {
    if (status === "guest") router.replace("/login");
  }, [status, router]);

  if (status === "loading" || status === "guest") {
    return (
      <div className="mx-auto max-w-3xl px-4 py-10">
        <Skeleton className="h-8 w-40" />
        <Skeleton className="mt-6 h-48 w-full" />
      </div>
    );
  }

  // 크리에이터 전용 탭 구성 — 주문 화면(Phase 4)에서 브랜드용 탭이 추가된다
  if (user?.account_type !== "CREATOR") {
    return (
      <div className="mx-auto max-w-3xl px-4 py-20 text-center text-muted-foreground">
        크리에이터 계정 전용 화면입니다. 브랜드용 주문 관리 화면은 곧 제공됩니다.
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-3xl px-4 py-10">
      <h1 className="text-2xl font-bold">크리에이터 대시보드</h1>
      <nav className="mt-6 flex gap-1 border-b">
        {TABS.map((tab) => (
          <Link
            key={tab.href}
            href={tab.href}
            className={
              pathname.startsWith(tab.href)
                ? "border-b-2 border-primary px-4 py-2 text-sm font-semibold"
                : "px-4 py-2 text-sm text-muted-foreground hover:text-foreground"
            }
          >
            {tab.label}
          </Link>
        ))}
      </nav>
      <div className="py-8">{children}</div>
    </div>
  );
}
