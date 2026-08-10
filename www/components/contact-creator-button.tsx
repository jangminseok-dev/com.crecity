"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";

import { Button } from "@/components/ui/button";
import { ApiError, apiFetch } from "@/lib/api";
import { useAuthStore } from "@/lib/auth-store";

/** 프로필의 "문의하기" — 브랜드 로그인 시에만 노출, 대화방 생성(재사용) 후 이동. */
export default function ContactCreatorButton({ slug }: { slug: string }) {
  const router = useRouter();
  const { status, user } = useAuthStore();
  // 단일 객체 상태 — 진행·오류
  const [state, setState] = useState<{ opening: boolean; error: string | null }>({
    opening: false,
    error: null,
  });

  if (status !== "authenticated" || user?.account_type !== "BRAND") return null;

  const openConversation = async () => {
    setState({ opening: true, error: null });
    try {
      const conversation = await apiFetch<{ id: number }>("/chat/conversations", {
        method: "POST",
        body: JSON.stringify({ creator_slug: slug }),
      });
      router.push(`/chat/${conversation.id}`);
    } catch (error) {
      setState({
        opening: false,
        error: error instanceof ApiError ? error.detail : "문의를 시작하지 못했습니다.",
      });
    }
  };

  return (
    <div>
      <Button variant="outline" size="sm" disabled={state.opening} onClick={openConversation}>
        {state.opening ? "여는 중…" : "💬 문의하기"}
      </Button>
      {state.error && <p className="mt-1 text-xs text-destructive">{state.error}</p>}
    </div>
  );
}
