"use client";

import Link from "next/link";

import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { useAuthStore } from "@/lib/auth-store";

/**
 * 계정 유형 전용 대시보드 화면 가드(갭 #93) — 다른 유형이 URL로 직접 열면
 * 상대 유형의 폼 대신 안내를 보여준다. 백엔드 403이 실해는 막고 있으므로
 * 이 가드는 보안 장치가 아니라 "왜 안 되는지"를 설명하는 UX 장치다.
 */
export default function AccountTypeGuard({
  require,
  feature,
  hint,
  children,
}: {
  require: "BRAND" | "CREATOR";
  feature: string;
  hint: { href: string; label: string };
  children: React.ReactNode;
}) {
  const user = useAuthStore((s) => s.user);

  if (!user) return <Skeleton className="h-40 w-full" />;

  if (user.account_type !== require) {
    return (
      <div className="rounded-xl border border-dashed px-6 py-14 text-center">
        {/* feature는 "…관리"류 명사로 끝난다 — 조사는 "는"으로 고정 */}
        <p className="font-semibold">
          {feature}는 {require === "BRAND" ? "브랜드" : "크리에이터"} 계정 기능입니다
        </p>
        <p className="mt-2 text-sm text-muted-foreground">
          지금 계정은 {user.account_type === "BRAND" ? "브랜드" : "크리에이터"} 계정이라 이
          화면을 쓸 수 없어요.
        </p>
        <Button
          variant="outline"
          className="mt-5"
          nativeButton={false}
          render={<Link href={hint.href}>{hint.label}</Link>}
        />
      </div>
    );
  }

  return <>{children}</>;
}
