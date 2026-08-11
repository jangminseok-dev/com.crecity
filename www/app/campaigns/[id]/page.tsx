"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { z } from "zod";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Skeleton } from "@/components/ui/skeleton";
import { Textarea } from "@/components/ui/textarea";
import { ApiError, apiFetch } from "@/lib/api";
import { useAuthStore } from "@/lib/auth-store";
import { PLATFORM_LABELS, formatKrw } from "@/lib/labels";
import type { Campaign, CampaignApplication } from "@/lib/types";

const applySchema = z.object({
  message: z.string().min(10, "제안 내용을 10자 이상 작성해 주세요."),
  proposed_price_krw: z.coerce.number().int().positive("견적은 0보다 커야 합니다."),
});

function ApplyForm({ campaignId }: { campaignId: number }) {
  // 단일 객체 상태 — 제출 진행·결과 메시지 (입력값은 FormData 패턴)
  const [form, setForm] = useState<{ submitting: boolean; error: string | null; done: boolean }>({
    submitting: false,
    error: null,
    done: false,
  });

  if (form.done) {
    return (
      <p className="rounded-md bg-muted p-4 text-sm text-muted-foreground">
        지원이 접수되었습니다 — 브랜드가 지원을 수락하면 제안 견적으로 주문이 시작됩니다.
      </p>
    );
  }

  const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    const parsed = applySchema.safeParse(Object.fromEntries(new FormData(e.currentTarget).entries()));
    if (!parsed.success) {
      setForm((prev) => ({ ...prev, error: parsed.error.issues[0].message }));
      return;
    }
    setForm((prev) => ({ ...prev, submitting: true, error: null }));
    try {
      await apiFetch(`/campaign/campaigns/${campaignId}/applications`, {
        method: "POST",
        body: JSON.stringify(parsed.data),
      });
      setForm({ submitting: false, error: null, done: true });
    } catch (error) {
      setForm({
        submitting: false,
        done: false,
        error: error instanceof ApiError ? error.detail : "지원에 실패했습니다.",
      });
    }
  };

  return (
    <Card>
      <CardContent className="p-5">
        <p className="font-semibold">이 공고에 지원하기</p>
        <form onSubmit={handleSubmit} className="mt-4 grid gap-4">
          <div className="grid gap-1.5">
            <Label htmlFor="proposed_price_krw">제안 견적 (원)</Label>
            <Input id="proposed_price_krw" name="proposed_price_krw" type="number" min={1} placeholder="400000" />
          </div>
          <div className="grid gap-1.5">
            <Label htmlFor="message">제안 내용</Label>
            <Textarea
              id="message"
              name="message"
              rows={4}
              placeholder="어떤 방향으로 제작할지, 일정·경험 등을 어필해 주세요."
            />
          </div>
          {form.error && <p className="text-sm text-destructive">{form.error}</p>}
          <Button type="submit" disabled={form.submitting} className="justify-self-start">
            {form.submitting ? "지원 중…" : "지원하기"}
          </Button>
        </form>
      </CardContent>
    </Card>
  );
}

function ApplicationList({ campaignId }: { campaignId: number }) {
  const { data: applications, isPending } = useQuery({
    queryKey: ["campaignApplications", campaignId],
    queryFn: () =>
      apiFetch<CampaignApplication[]>(`/campaign/campaigns/${campaignId}/applications`),
  });

  if (isPending) return <Skeleton className="h-32 w-full" />;
  if (!applications || applications.length === 0) {
    return (
      <p className="rounded-xl border border-dashed py-10 text-center text-sm text-muted-foreground">
        아직 지원자가 없습니다.
      </p>
    );
  }
  return (
    <div className="grid gap-3">
      <h3 className="font-semibold">지원자 ({applications.length})</h3>
      {applications.map((application) => (
        <Card key={application.id}>
          <CardContent className="grid gap-2 p-4">
            <div className="flex items-center justify-between gap-2">
              <Link
                href={`/creators/${application.creator_slug}`}
                target="_blank"
                className="font-medium underline-offset-2 hover:underline"
              >
                {application.creator_name} ↗
              </Link>
              <p className="font-semibold">{formatKrw(application.proposed_price_krw)}</p>
            </div>
            <p className="whitespace-pre-line text-sm text-muted-foreground">
              {application.message}
            </p>
            <div className="mt-1">
              {application.order_id ? (
                <Button
                  variant="outline"
                  size="sm"
                  nativeButton={false}
                  render={<Link href={`/dashboard/orders/${application.order_id}`}>✓ 수락됨 — 주문 보기</Link>}
                />
              ) : (
                <Button
                  size="sm"
                  nativeButton={false}
                  render={
                    <Link href={`/orders/new?application=${application.id}&campaign=${campaignId}`}>
                      수락하고 결제
                    </Link>
                  }
                />
              )}
            </div>
          </CardContent>
        </Card>
      ))}
    </div>
  );
}

export default function CampaignDetailPage() {
  const { id } = useParams<{ id: string }>();
  const { status, user } = useAuthStore();
  const queryClient = useQueryClient();

  const { data: campaign, isPending, error } = useQuery({
    queryKey: ["campaign", id],
    queryFn: () => apiFetch<Campaign>(`/campaign/campaigns/${id}`),
    enabled: status === "authenticated",
  });

  const closeCampaign = useMutation({
    mutationFn: () => apiFetch(`/campaign/campaigns/${id}/close`, { method: "POST" }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["campaign", id] }),
  });

  if (status === "guest") {
    return (
      <p className="mx-auto max-w-3xl px-4 py-20 text-center text-muted-foreground">
        로그인하면 공고를 볼 수 있습니다.
      </p>
    );
  }
  if (status === "loading" || isPending || !user) {
    return (
      <div className="mx-auto max-w-3xl px-4 py-10">
        <Skeleton className="h-64 w-full" />
      </div>
    );
  }
  if (error || !campaign) {
    return (
      <p className="mx-auto max-w-3xl px-4 py-20 text-center text-muted-foreground">
        공고를 찾을 수 없습니다.
      </p>
    );
  }

  const isOwner = campaign.brand_user_id === user.id;

  return (
    <div className="mx-auto max-w-3xl px-4 py-10">
      <div className="flex items-center gap-2">
        <h1 className="text-2xl font-bold tracking-[-0.02em]">{campaign.title}</h1>
        <Badge variant="outline">{PLATFORM_LABELS[campaign.platform]}</Badge>
        {campaign.status === "CLOSED" && <Badge variant="destructive">마감됨</Badge>}
      </div>
      <p className="mt-2 text-sm font-semibold">예산 {formatKrw(campaign.budget_krw)}</p>
      {(campaign.deadline_at || campaign.target_category || campaign.target_location) && (
        <div className="mt-2.5 flex flex-wrap gap-1.5">
          {campaign.deadline_at && (
            <Badge variant="outline">
              지원 마감 {new Date(campaign.deadline_at).toLocaleDateString("ko-KR")}
            </Badge>
          )}
          {campaign.target_category && <Badge variant="secondary">{campaign.target_category}</Badge>}
          {campaign.target_location && <Badge variant="secondary">{campaign.target_location}</Badge>}
        </div>
      )}
      <p className="mt-4 whitespace-pre-line text-sm">{campaign.description}</p>

      <div className="mt-8 grid gap-4">
        {isOwner ? (
          <>
            {campaign.status === "OPEN" && (
              <Button
                variant="outline"
                className="justify-self-start"
                disabled={closeCampaign.isPending}
                onClick={() => {
                  if (window.confirm("공고를 마감할까요? 이후 지원을 받을 수 없습니다.")) {
                    closeCampaign.mutate();
                  }
                }}
              >
                공고 마감하기
              </Button>
            )}
            <ApplicationList campaignId={campaign.id} />
          </>
        ) : user.account_type === "CREATOR" && campaign.status === "OPEN" ? (
          <ApplyForm campaignId={campaign.id} />
        ) : null}
      </div>
    </div>
  );
}
