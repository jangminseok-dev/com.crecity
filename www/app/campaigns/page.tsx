"use client";

import Link from "next/link";
import { useQuery } from "@tanstack/react-query";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { apiFetch } from "@/lib/api";
import { useAuthStore } from "@/lib/auth-store";
import { PLATFORM_LABELS, formatKrw } from "@/lib/labels";
import type { Campaign } from "@/lib/types";

export default function CampaignsPage() {
  const status = useAuthStore((s) => s.status);
  const { data: campaigns, isPending } = useQuery({
    queryKey: ["openCampaigns"],
    queryFn: () => apiFetch<Campaign[]>("/campaign/campaigns"),
    enabled: status === "authenticated",
  });

  if (status === "guest") {
    return (
      <div className="mx-auto max-w-3xl px-4 py-20 text-center">
        <p className="text-muted-foreground">캠페인 공고는 로그인하면 볼 수 있습니다.</p>
        <Button className="mt-4" nativeButton={false} render={<Link href="/login">로그인하기</Link>} />
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-3xl px-4 py-10">
      <h1 className="text-2xl font-bold">캠페인 공고</h1>
      <p className="mt-1 text-sm text-muted-foreground">
        브랜드가 올린 공고에 나만의 견적으로 지원해 보세요.
      </p>
      <div className="mt-6 grid gap-3">
        {status === "loading" || isPending ? (
          <Skeleton className="h-40 w-full" />
        ) : !campaigns || campaigns.length === 0 ? (
          <p className="rounded-lg border border-dashed py-16 text-center text-muted-foreground">
            지금은 열려 있는 공고가 없습니다.
          </p>
        ) : (
          campaigns.map((campaign) => (
            <Link key={campaign.id} href={`/campaigns/${campaign.id}`}>
              <Card className="transition-shadow hover:shadow-md">
                <CardContent className="flex items-center justify-between gap-4 p-4">
                  <div className="min-w-0">
                    <div className="flex items-center gap-2">
                      <Badge variant="outline">{PLATFORM_LABELS[campaign.platform]}</Badge>
                      <p className="truncate font-medium">{campaign.title}</p>
                    </div>
                    <p className="mt-1 line-clamp-1 text-sm text-muted-foreground">
                      {campaign.description}
                    </p>
                  </div>
                  <p className="shrink-0 text-sm font-semibold">
                    예산 {formatKrw(campaign.budget_krw)}
                  </p>
                </CardContent>
              </Card>
            </Link>
          ))
        )}
      </div>
    </div>
  );
}
