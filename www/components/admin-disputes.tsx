"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";

import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { ApiError, apiFetch } from "@/lib/api";
import { formatKrw } from "@/lib/labels";

type OpenDispute = {
  id: number;
  order_id: number;
  package_title: string;
  brand_user_id: number;
  creator_user_id: number;
  amount_krw: number;
  brand_total_krw: number;
  order_status: string;
  raised_by_user_id: number;
  reason: string;
  status: string;
  resolution: string | null;
  created_at: string | null;
};

const DECISIONS = [
  { path: "refund", label: "브랜드 환불", confirm: "브랜드에게 전액 환불하고 주문을 취소합니다." },
  { path: "release", label: "크리에이터 지급", confirm: "크리에이터에게 전액 지급하고 주문을 확정합니다." },
  { path: "dismiss", label: "기각", confirm: "주문을 그대로 두고 분쟁만 닫습니다." },
] as const;

/* 판정 코드 → 사람이 읽는 말(이력 표시용) */
const DECISION_LABELS: Record<string, string> = {
  REFUND: "브랜드 환불",
  RELEASE: "크리에이터 지급",
  DISMISS: "기각",
};

/** 분쟁 중재 — 판정은 전액 단위다(부분 배분 없음). dispute.resolve 권한. */
export default function AdminDisputes() {
  const queryClient = useQueryClient();
  // 단일 객체 상태 — 판정 실패 메시지 + 이력 보기(갭 #71)
  const [ui, setUi] = useState<{ error: string | null; showResolved: boolean }>({
    error: null,
    showResolved: false,
  });
  const { error, showResolved } = ui;
  const setError = (message: string | null) =>
    setUi((prev) => ({ ...prev, error: message }));
  const setShowResolved = (value: boolean) =>
    setUi((prev) => ({ ...prev, showResolved: value }));

  const { data: disputes } = useQuery({
    queryKey: ["disputes", showResolved],
    queryFn: () =>
      apiFetch<OpenDispute[]>(
        showResolved ? "/admin/disputes/resolved" : "/admin/disputes/open",
      ),
  });

  const resolve = useMutation({
    mutationFn: ({ id, path }: { id: number; path: string }) =>
      apiFetch(`/admin/disputes/${id}/${path}`, { method: "POST" }),
    onSuccess: async () => {
      setError(null);
      await queryClient.invalidateQueries({ queryKey: ["disputes"] });
    },
    onError: (err) => setError(err instanceof ApiError ? err.detail : "판정에 실패했습니다."),
  });

  return (
    <section className="mt-12">
      <h2 className="text-xl font-bold tracking-[-0.02em]">분쟁 중재</h2>
      <p className="mt-1 text-sm text-muted-foreground">
        신고 내용과 주문의 납품물을 확인한 뒤 판정하세요. 환불·지급은 되돌릴 수 없습니다.
      </p>
      <div className="mt-3 flex gap-1.5">
        {[
          { label: "판정 대기", resolved: false },
          { label: "판정 완료", resolved: true },
        ].map((tab) => (
          <button
            key={tab.label}
            type="button"
            onClick={() => setShowResolved(tab.resolved)}
            className={`inline-flex h-8 items-center rounded-full px-3.5 text-[13px] transition-colors ${
              showResolved === tab.resolved
                ? "bg-secondary font-semibold text-foreground"
                : "text-muted-foreground hover:text-foreground"
            }`}
          >
            {tab.label}
          </button>
        ))}
      </div>
      {error && <p className="mt-3 text-sm text-destructive">{error}</p>}
      <div className="mt-4 grid gap-3">
        {!disputes || disputes.length === 0 ? (
          <p className="rounded-xl border border-dashed py-10 text-center text-sm text-muted-foreground">
            {showResolved ? "판정한 분쟁이 없습니다." : "처리 대기 중인 분쟁이 없습니다."}
          </p>
        ) : (
          disputes.map((dispute) => (
            <Card key={dispute.id}>
              <CardContent className="grid gap-3 p-5">
                <div>
                  <p className="font-semibold">
                    주문 #{dispute.order_id} · {dispute.package_title}
                    <span className="ml-2 text-sm font-normal text-muted-foreground">
                      예치 {formatKrw(dispute.brand_total_krw)} · {dispute.order_status}
                    </span>
                  </p>
                  <p className="mt-1 text-sm text-muted-foreground">
                    신고자 user #{dispute.raised_by_user_id}
                    {dispute.raised_by_user_id === dispute.brand_user_id ? " (브랜드)" : " (크리에이터)"}
                    {dispute.created_at &&
                      ` · ${new Date(dispute.created_at).toLocaleString("ko-KR")}`}
                  </p>
                </div>
                <p className="whitespace-pre-wrap rounded-md bg-muted p-3 text-sm">
                  {dispute.reason}
                </p>
                {showResolved ? (
                  <p className="rounded-md bg-secondary px-3 py-2 text-[13px]">
                    판정: {DECISION_LABELS[dispute.resolution ?? ""] ?? dispute.resolution ?? "-"}
                  </p>
                ) : (
                <div className="flex flex-wrap gap-2">
                  {DECISIONS.map((decision) => (
                    <Button
                      key={decision.path}
                      size="sm"
                      variant={decision.path === "refund" ? "default" : "outline"}
                      disabled={resolve.isPending}
                      onClick={() => {
                        if (window.confirm(decision.confirm)) {
                          resolve.mutate({ id: dispute.id, path: decision.path });
                        }
                      }}
                    >
                      {decision.label}
                    </Button>
                  ))}
                </div>
                )}
              </CardContent>
            </Card>
          ))
        )}
      </div>
    </section>
  );
}
