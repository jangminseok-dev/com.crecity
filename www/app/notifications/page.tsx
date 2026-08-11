"use client";

import Link from "next/link";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { apiFetch } from "@/lib/api";
import { useAuthStore } from "@/lib/auth-store";
import type { NotificationsResult } from "@/lib/types";

export default function NotificationsPage() {
  const status = useAuthStore((s) => s.status);
  const queryClient = useQueryClient();

  const { data, isPending } = useQuery({
    queryKey: ["notifications"],
    queryFn: () => apiFetch<NotificationsResult>("/notification/notifications"),
    enabled: status === "authenticated",
  });

  const invalidate = () => queryClient.invalidateQueries({ queryKey: ["notifications"] });

  // 개별 읽음(갭 #34) — 항목을 열거나 점을 누르면 그 알림만 읽음이 된다
  const markRead = useMutation({
    mutationFn: (notificationId: number) =>
      apiFetch<void>(`/notification/notifications/${notificationId}/read`, { method: "POST" }),
    onSuccess: invalidate,
  });
  const markAllRead = useMutation({
    mutationFn: () =>
      apiFetch<void>("/notification/notifications/read-all", { method: "POST" }),
    onSuccess: invalidate,
  });

  if (status === "guest") {
    return (
      <div className="mx-auto max-w-2xl px-4 py-20 text-center">
        <p className="text-muted-foreground">알림은 로그인하면 볼 수 있습니다.</p>
        <Button className="mt-4" nativeButton={false} render={<Link href="/login">로그인하기</Link>} />
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-2xl px-4 py-10">
      <div className="flex items-center justify-between gap-3">
        <h1 className="text-2xl font-bold tracking-[-0.02em]">알림</h1>
        {(data?.unread_count ?? 0) > 0 && (
          <button
            type="button"
            onClick={() => markAllRead.mutate()}
            disabled={markAllRead.isPending}
            className="text-sm font-medium text-muted-foreground transition-colors hover:text-foreground"
          >
            모두 읽음 ({data?.unread_count})
          </button>
        )}
      </div>
      <div className="mt-6 grid gap-2">
        {status === "loading" || isPending ? (
          <Skeleton className="h-40 w-full" />
        ) : !data || data.items.length === 0 ? (
          <p className="rounded-xl border border-dashed py-16 text-center text-muted-foreground">
            아직 알림이 없습니다.
          </p>
        ) : (
          data.items.map((item) => {
            const card = (
              <Card className={item.link ? "transition-shadow hover:shadow-md" : undefined}>
                <CardContent className="flex items-start gap-3 p-4">
                  {!item.is_read && (
                    <button
                      type="button"
                      aria-label="읽음으로 표시"
                      onClick={(event) => {
                        event.preventDefault(); // 링크 이동 대신 읽음 처리만
                        markRead.mutate(item.id);
                      }}
                      className="mt-1.5 size-2 shrink-0 rounded-full bg-destructive"
                    />
                  )}
                  <div className="min-w-0">
                    <p className="text-sm">{item.body}</p>
                    {item.created_at && (
                      <p className="mt-0.5 text-xs text-muted-foreground">
                        {new Date(item.created_at).toLocaleString("ko-KR")}
                      </p>
                    )}
                  </div>
                </CardContent>
              </Card>
            );
            return item.link ? (
              <Link
                key={item.id}
                href={item.link}
                onClick={() => {
                  if (!item.is_read) markRead.mutate(item.id);
                }}
              >
                {card}
              </Link>
            ) : (
              <div key={item.id}>{card}</div>
            );
          })
        )}
      </div>
    </div>
  );
}
