"use client";

import Link from "next/link";
import { useQuery } from "@tanstack/react-query";

import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { apiFetch } from "@/lib/api";
import { useAuthStore } from "@/lib/auth-store";
import type { ChatConversation } from "@/lib/types";

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
      <h1 className="text-2xl font-bold">메시지</h1>
      <div className="mt-6 grid gap-2">
        {status === "loading" || isPending ? (
          <Skeleton className="h-40 w-full" />
        ) : !conversations || conversations.length === 0 ? (
          <p className="rounded-lg border border-dashed py-16 text-center text-muted-foreground">
            아직 대화가 없습니다 — 크리에이터 프로필의 "문의하기"로 시작해 보세요.
          </p>
        ) : (
          conversations.map((conversation) => (
            <Link key={conversation.id} href={`/chat/${conversation.id}`}>
              <Card className="transition-shadow hover:shadow-md">
                <CardContent className="flex items-center justify-between gap-4 p-4">
                  <div className="min-w-0">
                    <p className="font-medium">{conversation.counterpart_name}</p>
                    <p className="mt-0.5 truncate text-sm text-muted-foreground">
                      {conversation.last_message ?? "아직 메시지가 없습니다"}
                    </p>
                  </div>
                </CardContent>
              </Card>
            </Link>
          ))
        )}
      </div>
    </div>
  );
}
