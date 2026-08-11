"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useEffect, useRef } from "react";

import { ImagePlus, Send } from "lucide-react";

import OfferPanel from "@/components/offer-panel";
import { Skeleton } from "@/components/ui/skeleton";
import { ApiError, apiFetch } from "@/lib/api";
import { useAuthStore } from "@/lib/auth-store";
import type { ChatConversation, ChatMessage } from "@/lib/types";

/** 본문 속 http(s) URL을 클릭 가능한 링크로 렌더링 — React가 이스케이프하므로 별도 새니타이즈 불필요 */
function renderWithLinks(text: string) {
  return text.split(/(https?:\/\/[^\s]+)/g).map((part, index) =>
    part.startsWith("http://") || part.startsWith("https://") ? (
      <a
        key={index}
        href={part}
        target="_blank"
        rel="noopener noreferrer"
        className="break-all underline underline-offset-2"
      >
        {part}
      </a>
    ) : (
      part
    ),
  );
}

export default function ChatRoomPage() {
  const { id } = useParams<{ id: string }>();
  const { status, user } = useAuthStore();
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

  // 새 메시지를 볼 때마다 읽음 처리(갭 #35) — 목록의 안 읽음 뱃지가 따라 내려간다
  const lastMessageId = messages?.[messages.length - 1]?.id;
  useEffect(() => {
    if (status !== "authenticated" || !messages) return;
    void apiFetch<void>(`/chat/conversations/${id}/read`, { method: "POST" }).then(() =>
      queryClient.invalidateQueries({ queryKey: ["conversations"] }),
    );
  }, [status, id, lastMessageId, messages, queryClient]);

  const send = useMutation({
    mutationFn: (body: string) =>
      apiFetch<ChatMessage>(`/chat/conversations/${id}/messages`, {
        method: "POST",
        body: JSON.stringify({ body }),
      }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["messages", id] }),
  });
  const sendPhoto = useMutation({
    mutationFn: (file: File) => {
      const form = new FormData();
      form.append("file", file);
      return apiFetch<ChatMessage>(`/chat/conversations/${id}/photos`, {
        method: "POST",
        body: form,
      });
    },
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
      <div className="flex items-center gap-3 border-b pb-3">
        <span className="flex size-9 shrink-0 items-center justify-center rounded-full bg-secondary text-sm font-semibold text-secondary-foreground">
          {(conversation?.counterpart_name ?? "대").slice(0, 1)}
        </span>
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

      {status === "authenticated" && (
        <OfferPanel conversationId={id} isCreator={user?.account_type === "CREATOR"} />
      )}

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
              {message.image_url ? (
                <a
                  href={`/api/backend${message.image_url}`}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="max-w-[75%]"
                >
                  {/* eslint-disable-next-line @next/next/no-img-element */}
                  <img
                    src={`/api/backend${message.image_url}`}
                    alt="첨부 사진"
                    className="max-h-80 rounded-2xl border object-cover"
                  />
                </a>
              ) : (
                <p
                  className={`max-w-[75%] whitespace-pre-line rounded-2xl px-4 py-2 text-sm ${
                    message.is_mine ? "bg-primary text-primary-foreground" : "bg-muted"
                  }`}
                >
                  {renderWithLinks(message.body)}
                </p>
              )}
            </div>
          ))
        )}
        <div ref={bottomRef} />
      </div>

      <form onSubmit={handleSubmit} className="flex gap-2.5 border-t pt-3">
        <label
          aria-label="사진 첨부"
          className={`inline-flex size-11 shrink-0 cursor-pointer items-center justify-center rounded-full text-muted-foreground transition-colors hover:bg-secondary hover:text-foreground ${
            sendPhoto.isPending ? "pointer-events-none opacity-50" : ""
          }`}
        >
          <ImagePlus className="size-5" />
          <input
            type="file"
            accept="image/jpeg,image/png,image/webp"
            className="hidden"
            onChange={(e) => {
              const file = e.target.files?.[0];
              if (file) sendPhoto.mutate(file);
              e.target.value = ""; // 같은 파일 재선택 허용
            }}
          />
        </label>
        <input
          name="body"
          placeholder="메시지를 입력하세요"
          autoComplete="off"
          maxLength={2000}
          className="h-11 flex-1 rounded-full border px-4 text-sm outline-none transition-colors focus:border-primary"
        />
        <button
          type="submit"
          disabled={send.isPending}
          aria-label="보내기"
          className="inline-flex size-11 shrink-0 items-center justify-center rounded-full bg-primary text-primary-foreground transition-colors hover:bg-accent-foreground disabled:bg-muted disabled:text-muted-foreground"
        >
          <Send className="size-[18px]" />
        </button>
      </form>
      {(send.error || sendPhoto.error) && (
        <p className="mt-1 text-xs text-destructive">
          {[send.error, sendPhoto.error].map((error) =>
            error instanceof ApiError ? error.detail : error ? "전송에 실패했습니다." : null,
          )}
        </p>
      )}
    </div>
  );
}
