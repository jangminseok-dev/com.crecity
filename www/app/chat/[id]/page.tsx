"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useEffect, useRef } from "react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Skeleton } from "@/components/ui/skeleton";
import { ApiError, apiFetch } from "@/lib/api";
import { useAuthStore } from "@/lib/auth-store";
import type { ChatConversation, ChatMessage } from "@/lib/types";

export default function ChatRoomPage() {
  const { id } = useParams<{ id: string }>();
  const status = useAuthStore((s) => s.status);
  const queryClient = useQueryClient();
  const bottomRef = useRef<HTMLDivElement>(null);

  const { data: conversation } = useQuery({
    queryKey: ["conversation", id],
    queryFn: () => apiFetch<ChatConversation>(`/chat/conversations/${id}`),
    enabled: status === "authenticated",
  });
  const { data: messages, isPending } = useQuery({
    queryKey: ["messages", id],
    queryFn: () => apiFetch<ChatMessage[]>(`/chat/conversations/${id}/messages`),
    enabled: status === "authenticated",
    refetchInterval: 5_000, // 실시간 대신 주기 폴링 — 단순·크래시 안전
  });

  const send = useMutation({
    mutationFn: (body: string) =>
      apiFetch<ChatMessage>(`/chat/conversations/${id}/messages`, {
        method: "POST",
        body: JSON.stringify({ body }),
      }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["messages", id] }),
  });

  // 새 메시지 도착 시 맨 아래로
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages?.length]);

  if (status === "guest") {
    return (
      <p className="mx-auto max-w-2xl px-4 py-20 text-center text-muted-foreground">
        로그인하면 대화를 볼 수 있습니다.
      </p>
    );
  }

  const handleSubmit = (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    const formElement = e.currentTarget;
    const body = String(new FormData(formElement).get("body") ?? "").trim();
    if (!body) return;
    send.mutate(body, { onSuccess: () => formElement.reset() });
  };

  return (
    <div className="mx-auto flex h-[calc(100dvh-8rem)] max-w-2xl flex-col px-4 py-6">
      <div className="flex items-center gap-2 border-b pb-3">
        <h1 className="text-lg font-bold">{conversation?.counterpart_name ?? "대화"}</h1>
        {conversation?.counterpart_slug && (
          <Link
            href={`/creators/${conversation.counterpart_slug}`}
            className="text-sm text-muted-foreground underline underline-offset-2"
          >
            프로필 보기
          </Link>
        )}
      </div>

      <div className="flex-1 space-y-2 overflow-y-auto py-4">
        {isPending ? (
          <Skeleton className="h-40 w-full" />
        ) : !messages || messages.length === 0 ? (
          <p className="py-10 text-center text-sm text-muted-foreground">
            첫 메시지를 보내 협업을 시작해 보세요.
          </p>
        ) : (
          messages.map((message) => (
            <div
              key={message.id}
              className={`flex ${message.is_mine ? "justify-end" : "justify-start"}`}
            >
              <p
                className={`max-w-[75%] whitespace-pre-line rounded-2xl px-4 py-2 text-sm ${
                  message.is_mine ? "bg-primary text-primary-foreground" : "bg-muted"
                }`}
              >
                {message.body}
              </p>
            </div>
          ))
        )}
        <div ref={bottomRef} />
      </div>

      <form onSubmit={handleSubmit} className="flex gap-2 border-t pt-3">
        <Input name="body" placeholder="메시지 입력…" autoComplete="off" maxLength={2000} />
        <Button type="submit" disabled={send.isPending}>
          보내기
        </Button>
      </form>
      {send.error && (
        <p className="mt-1 text-xs text-destructive">
          {send.error instanceof ApiError ? send.error.detail : "전송에 실패했습니다."}
        </p>
      )}
    </div>
  );
}
