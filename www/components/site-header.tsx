"use client";

import { MessageCircle } from "lucide-react";
import Link from "next/link";
import { useState } from "react";

import NotificationBell from "@/components/notification-bell";
import { Skeleton } from "@/components/ui/skeleton";
import { useAuthStore } from "@/lib/auth-store";

export default function SiteHeader() {
  const { status, user, clearSession } = useAuthStore();
  const [menuOpen, setMenuOpen] = useState(false);

  const handleLogout = async () => {
    setMenuOpen(false);
    await fetch("/api/auth/logout", { method: "POST" });
    clearSession();
  };

  return (
    <header className="sticky top-0 z-50 border-b bg-background/90 backdrop-blur-md">
      <div className="mx-auto flex h-16 max-w-6xl items-center gap-2 px-6">
        <Link href="/" className="mr-5 text-[22px] font-extrabold tracking-[-0.04em]">
          crecity
        </Link>
        <nav className="flex items-center gap-0.5">
          <Link
            href="/"
            className="rounded-lg px-3 py-2 text-sm font-medium text-muted-foreground transition-colors hover:bg-secondary hover:text-foreground"
          >
            크리에이터 찾기
          </Link>
          {status === "authenticated" && (
            <Link
              href="/campaigns"
              className="rounded-lg px-3 py-2 text-sm font-medium text-muted-foreground transition-colors hover:bg-secondary hover:text-foreground"
            >
              캠페인
            </Link>
          )}
        </nav>

        <div className="ml-auto flex items-center gap-1">
          {status === "loading" && <Skeleton className="h-9 w-24" />}

          {status === "guest" && (
            <>
              <Link
                href="/login"
                className="px-2.5 py-2 text-sm font-medium text-muted-foreground transition-colors hover:text-foreground"
              >
                로그인
              </Link>
              <span className="h-3.5 w-px bg-border" aria-hidden />
              <Link
                href="/login"
                className="mr-1.5 px-2.5 py-2 text-sm font-medium text-muted-foreground transition-colors hover:text-foreground"
              >
                회원가입
              </Link>
              <Link
                href="/login"
                className="inline-flex h-9 items-center rounded-lg bg-accent px-4 text-sm font-semibold text-accent-foreground transition-colors hover:bg-[#dce4ff]"
              >
                크리에이터 등록
              </Link>
            </>
          )}

          {status === "authenticated" && user && (
            <>
              <Link
                href="/chat"
                aria-label="메시지"
                className="inline-flex size-10 items-center justify-center rounded-full text-muted-foreground transition-colors hover:bg-secondary hover:text-foreground"
              >
                <MessageCircle className="size-5" />
              </Link>
              <NotificationBell />
              <div className="relative ml-1.5">
                <button
                  type="button"
                  aria-label="계정 메뉴"
                  onClick={() => setMenuOpen(!menuOpen)}
                  className="flex size-[34px] items-center justify-center rounded-full bg-secondary text-sm font-semibold text-secondary-foreground"
                >
                  {user.email.slice(0, 1).toUpperCase()}
                </button>
                {menuOpen && (
                  <div className="absolute right-0 top-12 z-50 flex w-52 flex-col rounded-xl border bg-card p-1.5 shadow-raised">
                    <div className="mb-1 border-b px-3 pb-2 pt-2.5">
                      <p className="truncate text-xs text-muted-foreground">{user.email}</p>
                    </div>
                    <Link
                      href={
                        user.account_type === "CREATOR" ? "/dashboard/profile" : "/dashboard/orders"
                      }
                      onClick={() => setMenuOpen(false)}
                      className="rounded-lg px-3 py-2.5 text-left text-sm transition-colors hover:bg-muted"
                    >
                      대시보드
                    </Link>
                    {user.permissions.includes("profile.review") && (
                      <Link
                        href="/admin"
                        onClick={() => setMenuOpen(false)}
                        className="rounded-lg px-3 py-2.5 text-left text-sm transition-colors hover:bg-muted"
                      >
                        관리자
                      </Link>
                    )}
                    <hr className="mx-1 my-1.5" />
                    <button
                      type="button"
                      onClick={handleLogout}
                      className="rounded-lg px-3 py-2.5 text-left text-sm text-muted-foreground transition-colors hover:bg-muted"
                    >
                      로그아웃
                    </button>
                  </div>
                )}
              </div>
            </>
          )}
        </div>
      </div>
    </header>
  );
}
