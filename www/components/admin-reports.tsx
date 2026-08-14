"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import Link from "next/link";
import { useState } from "react";

import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { ApiError, apiFetch } from "@/lib/api";

type Report = {
  id: number;
  reporter_user_id: number;
  target_type: "PROFILE" | "CONVERSATION";
  target_id: number;
  reason: string;
  status: string;
  resolution_note: string;
  created_at: string | null;
  resolved_at: string | null;
};

const TARGET_LABELS: Record<Report["target_type"], string> = {
  PROFILE: "프로필",
  CONVERSATION: "대화방",
};

/** 어뷰징 신고 처리 큐(갭 #54) — report.review 권한. 조치 자체는 별도 기능으로 한다. */
export default function AdminReports() {
  const queryClient = useQueryClient();
  // 단일 값 상태 — 처리 실패 메시지
  const [error, setError] = useState<string | null>(null);

  const { data: reports } = useQuery({
    queryKey: ["openReports"],
    queryFn: () => apiFetch<Report[]>("/admin/reports/open"),
  });

  const resolve = useMutation({
    mutationFn: ({ id, note }: { id: number; note: string }) =>
      apiFetch(`/admin/reports/${id}/resolve`, {
        method: "POST",
        body: JSON.stringify({ note }),
      }),
    onSuccess: async () => {
      setError(null);
      await queryClient.invalidateQueries({ queryKey: ["openReports"] });
    },
    onError: (err) =>
      setError(err instanceof ApiError ? err.detail : "신고 처리에 실패했습니다."),
  });

  return (
    <section className="mt-12">
      <h2 className="text-xl font-bold tracking-[-0.02em]">
        신고 처리 {reports && reports.length > 0 && `(${reports.length})`}
      </h2>
      <p className="mt-1 text-sm text-muted-foreground">
        주문 안의 다툼은 분쟁 중재에서, 그 밖의 어뷰징은 여기서 처리합니다. 조치 내용을 메모로
        남기고 닫습니다.
      </p>
      {error && <p className="mt-3 text-sm text-destructive">{error}</p>}

      {!reports || reports.length === 0 ? (
        <p className="mt-4 rounded-xl border border-dashed py-10 text-center text-sm text-muted-foreground">
          처리 대기 중인 신고가 없습니다.
        </p>
      ) : (
        <div className="mt-4 grid gap-3">
          {reports.map((report) => (
            <Card key={report.id}>
              <CardContent className="p-4">
                <div className="flex flex-wrap items-center gap-2 text-sm">
                  <span className="rounded-full bg-secondary px-2.5 py-1 text-xs font-semibold">
                    {TARGET_LABELS[report.target_type]} {report.target_id}
                  </span>
                  <span className="text-xs text-muted-foreground">
                    신고자 {report.reporter_user_id}
                    {report.created_at && ` · ${report.created_at.slice(0, 10)}`}
                  </span>
                  {report.target_type === "CONVERSATION" && (
                    <Link
                      href={`/chat/${report.target_id}`}
                      className="text-xs text-primary underline underline-offset-2"
                    >
                      대화 열기
                    </Link>
                  )}
                </div>
                <p className="mt-2 whitespace-pre-line text-sm">{report.reason}</p>
                <form
                  className="mt-3 flex flex-wrap gap-2"
                  onSubmit={(event) => {
                    event.preventDefault();
                    const note = String(
                      new FormData(event.currentTarget).get("note") ?? ""
                    ).trim();
                    resolve.mutate({ id: report.id, note });
                  }}
                >
                  <Input
                    name="note"
                    placeholder="조치 내용 (예: 프로필 소유자에게 안내함)"
                    className="h-9 max-w-md flex-1"
                  />
                  <Button type="submit" size="sm" disabled={resolve.isPending}>
                    처리 완료
                  </Button>
                </form>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </section>
  );
}
