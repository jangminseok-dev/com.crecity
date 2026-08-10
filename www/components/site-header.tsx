"use client";

import Link from "next/link";

import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { useAuthStore } from "@/lib/auth-store";

export default function SiteHeader() {
  const { status, user, clearSession } = useAuthStore();

  const handleLogout = async () => {
    await fetch("/api/auth/logout", { method: "POST" });
    clearSession();
  };

  return (
    <header className="border-b">
      <div className="mx-auto flex h-14 max-w-5xl items-center justify-between px-4">
        <Link href="/" className="text-lg font-bold tracking-tight">
          crecity
        </Link>
        <nav className="flex items-center gap-2">
          {status === "loading" && <Skeleton className="h-8 w-20" />}
          {status === "guest" && (
            <Button size="sm" nativeButton={false} render={<Link href="/login">시작하기</Link>} />
          )}
          {status === "authenticated" && user && (
            <>
              {user.permissions.includes("profile.review") && (
                <Button
                  variant="ghost"
                  size="sm"
                  nativeButton={false}
                  render={<Link href="/admin">관리자</Link>}
                />
              )}
              <Button
                variant="ghost"
                size="sm"
                nativeButton={false}
                render={
                  <Link
                    href={
                      user.account_type === "CREATOR" ? "/dashboard/profile" : "/dashboard/orders"
                    }
                  >
                    대시보드
                  </Link>
                }
              />
              <span className="text-sm text-muted-foreground">{user.email}</span>
              <Button variant="outline" size="sm" onClick={handleLogout}>
                로그아웃
              </Button>
            </>
          )}
        </nav>
      </div>
    </header>
  );
}
