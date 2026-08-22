"use client";

import Link from "next/link";
import { useQuery } from "@tanstack/react-query";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { apiFetch } from "@/lib/api";
import { formatKrw } from "@/lib/labels";
import type { MyCampaignApplication } from "@/lib/types";

/**
 * 크리에이터 "내 지원 내역"(갭 #103).
 *
 * 지원 상태는 별도 컬럼이 아니라 **주문 생성 여부와 공고 상태**에서 파생한다 —
 * 같은 사실을 두 곳에 두지 않기 위해서다. 마감일이 지났으면 스윕 주기와 무관하게
 * 마감으로 본다(백엔드 `ensure_open_for_application`과 같은 기준).
 */
function statusOf(application: MyCampaignApplication) {
  if (application.order_id) {
    return { label: "선정 — 주문 시작", variant: "default" as const };
  }
  const closed =
    application.campaign_status === "CLOSED" ||
    (application.campaign_deadline_at !== null &&
      new Date(application.campaign_deadline_at) <= new Date());
  if (closed) return { label: "미선정 (공고 마감)", variant: "outline" as const };
  return { label: "검토 대기", variant: "secondary" as const };
}

export default function MyApplications() {
  const { data: applications, isPending } = useQuery({
    queryKey: ["myApplications"],
    queryFn: () => apiFetch<MyCampaignApplication[]>("/campaign/my/applications"),
  });

  if (isPending) return <Skeleton className="h-40 w-full" />;
  if (!applications) return null;

  if (applications.length === 0) {
    return (
      <div className="rounded-xl border border-dashed px-6 py-14 text-center">
        <p className="font-semibold">아직 지원한 공고가 없습니다</p>
        <p className="mt-2 text-sm text-muted-foreground">
          브랜드가 올린 공고에 나만의 견적으로 지원해 보세요.
        </p>
        <Button
          variant="outline"
          className="mt-5"
          nativeButton={false}
          render={<Link href="/campaigns">공고 둘러보기</Link>}
        />
      </div>
    );
  }

  return (
    <div className="grid gap-3">
      {applications.map((application) => {
        const status = statusOf(application);
        return (
          <Card key={application.id}>
            <CardContent className="p-5">
              <div className="flex flex-wrap items-center justify-between gap-2">
                <Link
                  href={`/campaigns/${application.campaign_id}`}
                  className="font-semibold hover:underline"
                >
                  {application.campaign_title}
                </Link>
                <Badge variant={status.variant}>{status.label}</Badge>
              </div>
              <p className="mt-2 text-sm text-muted-foreground">
                제안 견적 {formatKrw(application.proposed_price_krw)}
                {application.created_at &&
                  ` · ${new Date(application.created_at).toLocaleDateString("ko-KR")} 지원`}
              </p>
              <p className="mt-3 whitespace-pre-wrap text-sm">{application.message}</p>
              {/* 선정된 지원은 주문으로 이어진다 — 실제로 일을 진행하는 화면으로 보낸다 */}
              {application.order_id && (
                <Button
                  variant="outline"
                  size="sm"
                  className="mt-4"
                  nativeButton={false}
                  render={
                    <Link href={`/dashboard/orders/${application.order_id}`}>주문 보기</Link>
                  }
                />
              )}
            </CardContent>
          </Card>
        );
      })}
    </div>
  );
}
