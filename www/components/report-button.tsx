"use client";

import { useMutation } from "@tanstack/react-query";
import { useState } from "react";

import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { ApiError, apiFetch } from "@/lib/api";
import { useAuthStore } from "@/lib/auth-store";

/**
 * 어뷰징 신고(갭 #54) — 주문 안의 다툼은 분쟁으로, 그 밖의 일은 여기로.
 * 로그인한 사용자에게만 보인다(신고자를 특정할 수 없으면 처리할 수 없다).
 */
export default function ReportButton({
  targetType,
  targetId,
  label = "신고",
}: {
  targetType: "PROFILE" | "CONVERSATION";
  targetId: number;
  label?: string;
}) {
  const status = useAuthStore((state) => state.status);
  // 단일 객체 상태 — 열림·완료·오류 (사유는 FormData 패턴)
  const [state, setState] = useState<{ open: boolean; done: boolean; error: string | null }>({
    open: false,
    done: false,
    error: null,
  });

  const mutation = useMutation({
    mutationFn: (reason: string) =>
      apiFetch("/admin/reports", {
        method: "POST",
        body: JSON.stringify({ target_type: targetType, target_id: targetId, reason }),
      }),
    onSuccess: () => setState({ open: false, done: true, error: null }),
    onError: (error) =>
      setState((prev) => ({
        ...prev,
        error:
          error instanceof ApiError ? error.detail : "신고 접수에 실패했습니다.",
      })),
  });

  if (status !== "authenticated") return null;
  if (state.done) {
    return <span className="text-xs text-muted-foreground">신고가 접수되었습니다</span>;
  }
  if (!state.open) {
    return (
      <button
        type="button"
        onClick={() => setState({ open: true, done: false, error: null })}
        className="text-xs text-muted-foreground underline underline-offset-2 hover:text-foreground"
      >
        {label}
      </button>
    );
  }

  return (
    <form
      className="grid gap-2 rounded-lg border p-3"
      onSubmit={(event) => {
        event.preventDefault();
        const reason = String(new FormData(event.currentTarget).get("reason") ?? "").trim();
        if (reason.length < 10) {
          setState((prev) => ({ ...prev, error: "무엇이 문제인지 10자 이상 적어 주세요." }));
          return;
        }
        mutation.mutate(reason);
      }}
    >
      <Textarea
        name="reason"
        rows={3}
        maxLength={2000}
        placeholder="어떤 점이 문제인지 구체적으로 적어 주세요. 운영자가 확인 후 조치합니다."
      />
      {state.error && <p className="text-xs text-destructive">{state.error}</p>}
      <div className="flex gap-2">
        <Button type="submit" size="sm" disabled={mutation.isPending}>
          {mutation.isPending ? "접수 중…" : "신고 접수"}
        </Button>
        <Button
          type="button"
          variant="outline"
          size="sm"
          onClick={() => setState({ open: false, done: false, error: null })}
        >
          취소
        </Button>
      </div>
    </form>
  );
}
