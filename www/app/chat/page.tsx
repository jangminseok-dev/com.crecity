"use client";

import Link from "next/link";
import { useQuery } from "@tanstack/react-query";

import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { apiFetch } from "@/lib/api";
import { useAuthStore } from "@/lib/auth-store";
import type { ChatConversation } from "@/lib/types";

function formatTime(iso: string | null): string {
  if (!iso) return "";
  const date = new Date(iso);
  const today = new Date();
  const sameDay = date.toDateString() === today.toDateString();
  return sameDay
    ? date.toLocaleTimeString("ko-KR", { hour: "numeric", minute: "2-digit" })
    : date.toLocaleDateString("ko-KR", { month: "long", day: "numeric" });
}

export default function ChatListPage() {
  const status = useAuthStore((s) => s.status);
  const { data: conversations, isPending } = useQuery({
    queryKey: ["conversations"],
    queryFn: () => apiFetch<ChatConversation[]>("/chat/conversations"),
    enabled: status === "authenticated",
    refetchInterval: 10_000, // 폴링 — 새 대화·메시지 미리보기 갱신
  });

  if (status === "guest") {
    return (
      <div className="mx-auto max-w-2xl px-4 py-20 text-center">
        <p className="text-muted-foreground">메시지는 로그인하면 볼 수 있습니다.</p>
        <Button className="mt-4" nativeButton={false} render={<Link href="/login">로그인하기</Link>} />
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-2xl px-4 py-10">
      <h1 className="text-2xl font-bold tracking-[-0.02em]">메시지</h1>
      <div className="mt-4">
        {status === "loading" || isPending ? (
          <Skeleton className="h-40 w-full" />
        ) : !conversations || conversations.length === 0 ? (
          <p className="rounded-xl border border-dashed py-16 text-center text-muted-foreground">
            아직 대화가 없습니다 — 크리에이터 프로필의 "문의하기"로 시작해 보세요.
          </p>
        ) : (
          conversations.map((conversation) => (
            <Link
              key={conversation.id}
              href={`/chat/${conversation.id}`}
              className="flex items-center gap-3 rounded-xl px-3 py-3 transition-colors hover:bg-muted/50"
            >
              <span className="flex size-10 shrink-0 items-center justify-center rounded-full bg-secondary text-sm font-semibold text-secondary-foreground">
                {conversation.counterpart_name.slice(0, 1)}
              </span>
              <span className="min-w-0 flex-1">
                <span className="flex items-baseline justify-between gap-2">
                  <span className="text-sm font-semibold">{conversation.counterpart_name}</span>
                  <span className="shrink-0 text-xs text-muted-foreground/70">
                    {formatTime(conversation.last_message_at)}
                  </span>
                </span>
                <span className="mt-0.5 block truncate text-[13px] text-muted-foreground">
                  {conversation.last_message ?? "아직 메시지가 없습니다"}
                </span>
              </span>
            </Link>
          ))
        )}
      </div>
    </div>
  );
}
