"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";

import { ApiError, apiFetch } from "@/lib/api";

/** 주문 상세의 "대화 열기"(갭 #95) — 당사자면 크리에이터도 열 수 있다(기존 대화 재사용). */
export default function OrderChatButton({ orderId }: { orderId: number }) {
  const router = useRouter();
  // 단일 객체 상태 — 진행·오류
  const [state, setState] = useState<{ opening: boolean; error: string | null }>({
    opening: false,
    error: null,
  });

  const openConversation = async () => {
    setState({ opening: true, error: null });
    try {
      const conversation = await apiFetch<{ id: number }>(`/chat/conversations/order/${orderId}`, {
        method: "POST",
      });
      router.push(`/chat/${conversation.id}`);
    } catch (error) {
      setState({
        opening: false,
        error: error instanceof ApiError ? error.detail : "대화를 열지 못했습니다.",
      });
    }
  };

  return (
    <span className="inline-flex items-center gap-2">
      <button
        type="button"
        disabled={state.opening}
        onClick={openConversation}
        className="text-sm font-semibold text-primary underline-offset-2 hover:underline disabled:opacity-50"
      >
        {state.opening ? "여는 중…" : "💬 대화 열기"}
      </button>
      {state.error && <span className="text-xs text-destructive">{state.error}</span>}
    </span>
  );
}
