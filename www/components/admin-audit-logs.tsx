"use client";

import { useQuery } from "@tanstack/react-query";

import { Card, CardContent } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { apiFetch } from "@/lib/api";

type AuditLog = {
  id: number;
  subject: string;
  note: string;
  created_at: string | null;
};

const SUBJECT_LABELS: Record<string, string> = {
  profile_review: "프로필 심사",
  withdrawal_settlement: "인출 처리",
  steward: "운영",
};

/** 운영 감사 로그(갭 #36) — 심사·인출 처리 이력을 최신순으로 확인한다. */
export default function AdminAuditLogs() {
  const { data: logs, isPending } = useQuery({
    queryKey: ["adminAuditLogs"],
    queryFn: () => apiFetch<AuditLog[]>("/admin/audit-logs"),
  });

  return (
    <section className="mt-12">
      <h2 className="text-xl font-bold tracking-[-0.02em]">감사 로그</h2>
      <p className="mt-1 text-sm text-muted-foreground">
        운영자가 처리한 심사·인출 이력입니다(최근 200건, 수정·삭제 불가).
      </p>
      <div className="mt-4">
        {isPending ? (
          <Skeleton className="h-32 w-full" />
        ) : !logs || logs.length === 0 ? (
          <p className="rounded-xl border border-dashed py-10 text-center text-sm text-muted-foreground">
            아직 기록이 없습니다.
          </p>
        ) : (
          <Card>
            <CardContent className="divide-y p-0">
              {logs.map((log) => (
                <div key={log.id} className="flex items-start gap-3 px-4 py-3 text-sm">
                  <span className="mt-0.5 inline-flex shrink-0 rounded-md bg-secondary px-2 py-0.5 text-[11px] font-semibold text-secondary-foreground">
                    {SUBJECT_LABELS[log.subject] ?? log.subject}
                  </span>
                  <span className="min-w-0 flex-1">{log.note}</span>
                  {log.created_at && (
                    <span className="shrink-0 text-xs text-muted-foreground/70">
                      {new Date(log.created_at).toLocaleString("ko-KR")}
                    </span>
                  )}
                </div>
              ))}
            </CardContent>
          </Card>
        )}
      </div>
    </section>
  );
}
