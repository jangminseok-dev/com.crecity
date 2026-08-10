"use client";

import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import { Bell } from "lucide-react";

import { Button } from "@/components/ui/button";
import { apiFetch } from "@/lib/api";
import { useAuthStore } from "@/lib/auth-store";
import type { NotificationsResult } from "@/lib/types";

export default function NotificationBell() {
  const status = useAuthStore((s) => s.status);
  const { data } = useQuery({
    queryKey: ["notifications"],
    queryFn: () => apiFetch<NotificationsResult>("/notification/notifications"),
    enabled: status === "authenticated",
    refetchInterval: 30_000, // 폴링 — 실시간 채널 없이 안 읽음 뱃지 갱신
  });

  const unread = data?.unread_count ?? 0;
  return (
    <Button
      variant="ghost"
      size="sm"
      nativeButton={false}
      render={
        <Link href="/notifications" aria-label="알림" className="relative">
          <Bell className="size-4" />
          {unread > 0 && (
            <span className="absolute -right-1 -top-1 flex h-4 min-w-4 items-center justify-center rounded-full bg-destructive px-1 text-[10px] font-semibold text-white">
              {unread > 99 ? "99+" : unread}
            </span>
          )}
        </Link>
      }
    />
  );
}
