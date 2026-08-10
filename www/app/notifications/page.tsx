"use client";

import { useEffect, useRef } from "react";
import Link from "next/link";
import { useQuery, useQueryClient } from "@tanstack/react-query";

import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { apiFetch } from "@/lib/api";
import { useAuthStore } from "@/lib/auth-store";
import type { NotificationsResult } from "@/lib/types";

export default function NotificationsPage() {
  const status = useAuthStore((s) => s.status);
  const queryClient = useQueryClient();
  const markedRef = useRef(false); // StrictMode 이중 실행 가드

  const { data, isPending } = useQuery({
    queryKey: ["notifications"],
    queryFn: () => apiFetch<NotificationsResult>("/notification/notifications"),
    enabled: status === "authenticated",
  });

  // 페이지를 열면 모두 읽음 처리 — 목록의 안 읽음 표시는 유지하고 뱃지만 갱신한다.
  useEffect(() => {
    if (status !== "authenticated" || markedRef.current) return;
    markedRef.current = true;
    apiFetch<void>("/notification/notifications/read-all", { method: "POST" }).then(() =>
      queryClient.invalidateQueries({ queryKey: ["notifications"] }),
    );
  }, [status, queryClient]);

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
      <h1 className="text-2xl font-bold">알림</h1>
      <div className="mt-6 grid gap-2">
        {status === "loading" || isPending ? (
          <Skeleton className="h-40 w-full" />
        ) : !data || data.items.length === 0 ? (
          <p className="rounded-lg border border-dashed py-16 text-center text-muted-foreground">
            아직 알림이 없습니다.
          </p>
        ) : (
          data.items.map((item) => {
            const card = (
              <Card className={item.link ? "transition-shadow hover:shadow-md" : undefined}>
                <CardContent className="flex items-start gap-3 p-4">
                  {!item.is_read && (
                    <span className="mt-1.5 size-2 shrink-0 rounded-full bg-destructive" />
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
              <Link key={item.id} href={item.link}>
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
