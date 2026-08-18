"use client";

import Link from "next/link";
import { useQuery } from "@tanstack/react-query";

import { Button } from "@/components/ui/button";
import { fetchAnalytics, fetchProfile, maxEngagementPermille } from "@/lib/creator-metrics";
import { formatAcceptDuration, formatFollowers, formatKrw } from "@/lib/labels";
import type { CampaignApplication } from "@/lib/types";

function CompareRow({
  application,
  campaignId,
}: {
  application: CampaignApplication;
  campaignId: number;
}) {
  const slug = application.creator_slug;
  // 공개 프로필 API 조합(#83과 같은 원칙 — 백엔드 변경 없음). 프로필이 끊긴 지원자는 조회하지 않는다.
  const { data: profile } = useQuery({
    queryKey: ["creatorProfile", slug],
    queryFn: () => fetchProfile(slug),
    enabled: slug !== "",
  });
  const { data: analytics } = useQuery({
    queryKey: ["creatorAnalytics", slug],
    queryFn: () => fetchAnalytics(slug),
    enabled: slug !== "",
  });

  const engagement = analytics ? maxEngagementPermille(analytics) : null;

  return (
    <tr>
      <td className="border-b py-3.5 pr-3">
        {slug ? (
          <Link
            href={`/creators/${slug}`}
            target="_blank"
            className="font-semibold underline-offset-2 hover:underline"
          >
            {application.creator_name} ↗
          </Link>
        ) : (
          <span className="font-semibold">{application.creator_name}</span>
        )}
        {(profile?.trusted_creator || profile?.fast_responder) && (
          <span className="mt-0.5 block text-xs text-muted-foreground">
            {profile.trusted_creator && "🛡️ 신뢰 크리에이터"}
            {profile.trusted_creator && profile.fast_responder && " · "}
            {profile.fast_responder && "⚡ 빠른 응답"}
          </span>
        )}
      </td>
      <td className="border-b py-3.5 pr-3 font-semibold">
        {formatKrw(application.proposed_price_krw)}
      </td>
      <td className="border-b py-3.5 pr-3">
        {profile && profile.followers_total > 0 ? formatFollowers(profile.followers_total) : "—"}
      </td>
      <td className="border-b py-3.5 pr-3">
        {engagement !== null ? `${(engagement / 10).toFixed(1)}%` : "—"}
      </td>
      <td className="border-b py-3.5 pr-3">
        {profile && profile.completed_orders !== null ? `${profile.completed_orders}건` : "—"}
      </td>
      <td className="border-b py-3.5 pr-3">
        {profile && profile.avg_accept_hours !== null
          ? formatAcceptDuration(profile.avg_accept_hours)
          : "—"}
      </td>
      <td className="border-b py-3.5 text-right">
        {application.order_id ? (
          <Button
            variant="outline"
            size="sm"
            nativeButton={false}
            render={<Link href={`/dashboard/orders/${application.order_id}`}>✓ 수락됨</Link>}
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
      </td>
    </tr>
  );
}

/**
 * 지원자 나란히 비교(갭 #86) — 단가·팔로워·참여율·거래 실적을 한 표에서 본다.
 * 지표는 공개 프로필과 같은 값(자가입력 팔로워·참여율 포함)이며, 없는 값은 "—"로 둔다
 * (숫자를 만들지 않는다). 정렬·필터(#70)는 카드 목록과 공유한다.
 */
export default function CampaignApplicantCompare({
  applications,
  campaignId,
}: {
  applications: CampaignApplication[];
  campaignId: number;
}) {
  return (
    <div className="overflow-x-auto">
      <table className="w-full min-w-[720px] border-separate border-spacing-0 text-sm">
        <thead>
          <tr className="text-left text-muted-foreground">
            <th className="border-b pb-2.5 pr-3 font-medium">지원자</th>
            <th className="border-b pb-2.5 pr-3 font-medium">제안 견적</th>
            <th className="border-b pb-2.5 pr-3 font-medium">팔로워</th>
            <th className="border-b pb-2.5 pr-3 font-medium">참여율</th>
            <th className="border-b pb-2.5 pr-3 font-medium">완료 거래</th>
            <th className="border-b pb-2.5 pr-3 font-medium">평균 수락</th>
            <th className="border-b pb-2.5" />
          </tr>
        </thead>
        <tbody>
          {applications.map((application) => (
            <CompareRow key={application.id} application={application} campaignId={campaignId} />
          ))}
        </tbody>
      </table>
      <p className="mt-2 text-xs text-muted-foreground">
        팔로워·참여율은 크리에이터가 등록한 채널 지표(참여율은 채널 중 최고값)이며, 제안 내용은
        카드 보기에서 확인할 수 있습니다.
      </p>
    </div>
  );
}
