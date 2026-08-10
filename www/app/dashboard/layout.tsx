"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useEffect } from "react";

import { Skeleton } from "@/components/ui/skeleton";
import { useAuthStore } from "@/lib/auth-store";

const CREATOR_TABS = [
  { href: "/dashboard/profile", label: "내 프로필" },
  { href: "/dashboard/packages", label: "판매 패키지" },
  { href: "/dashboard/orders", label: "주문 관리" },
  { href: "/dashboard/balance", label: "잔액" },
];

const BRAND_TABS = [
  { href: "/dashboard/orders", label: "주문 관리" },
  { href: "/dashboard/campaigns", label: "내 공고" },
  { href: "/dashboard/balance", label: "크레딧" },
];

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  const { status, user } = useAuthStore();
  const router = useRouter();
  const pathname = usePathname();

  useEffect(() => {
    if (status === "guest") router.replace("/login");
  }, [status, router]);

  if (status === "loading" || status === "guest" || !user) {
    return (
      <div className="mx-auto max-w-3xl px-4 py-10">
        <Skeleton className="h-8 w-40" />
        <Skeleton className="mt-6 h-48 w-full" />
      </div>
    );
  }

  const isCreator = user.account_type === "CREATOR";
  const tabs = isCreator ? CREATOR_TABS : BRAND_TABS;

  return (
    <div className="mx-auto max-w-3xl px-4 py-10">
      <h1 className="text-2xl font-bold">{isCreator ? "크리에이터 대시보드" : "브랜드 대시보드"}</h1>
      <nav className="mt-6 flex gap-1 border-b">
        {tabs.map((tab) => (
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
