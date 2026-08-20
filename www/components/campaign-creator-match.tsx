"use client";

import { useQuery } from "@tanstack/react-query";

import CreatorCard from "@/components/creator-card";
import { apiFetch } from "@/lib/api";
import type { Campaign, CampaignApplication, ProfileListingItem } from "@/lib/types";

const MATCH_LIMIT = 4;

/**
 * 캠페인 적합 크리에이터 추천(갭 #99, §3.2 Instant Creator Match의 규칙 기반판) —
 * 공고의 타겟 조건(플랫폼·카테고리·지역)과 예산 이하 패키지를 가진 크리에이터를
 * 기존 공개 목록 필터로 보여준다. **표시만 한다** — 자동 초대·발송은 수락 강요가 된다.
 * 이미 지원한 크리에이터는 뺀다(지원자 목록이 그들의 자리다).
 */
export default function CampaignCreatorMatch({ campaign }: { campaign: Campaign }) {
  const { data: candidates } = useQuery({
    queryKey: ["campaignMatch", campaign.id],
    queryFn: () => {
      const query = new URLSearchParams({
        platform: campaign.platform,
        price_max: String(campaign.budget_krw),
        limit: String(MATCH_LIMIT * 2), // 지원자 제외 여유분
        ...(campaign.target_category ? { category: campaign.target_category } : {}),
        ...(campaign.target_location ? { location: campaign.target_location } : {}),
      });
      return apiFetch<{ items: ProfileListingItem[] }>(`/creator/profiles?${query}`);
    },
  });
  const { data: applications } = useQuery({
    queryKey: ["campaignApplications", campaign.id, { sort: "oldest", onlyOpen: false }],
    queryFn: () =>
      apiFetch<CampaignApplication[]>(`/campaign/campaigns/${campaign.id}/applications?sort=oldest`),
  });

  if (!candidates || !applications) return null;
  const applied = new Set(applications.map((application) => application.creator_slug));
  const matches = candidates.items.filter((item) => !applied.has(item.slug)).slice(0, MATCH_LIMIT);
  if (matches.length === 0) return null; // 후보가 없으면 섹션을 그리지 않는다

  return (
    <div className="grid gap-3">
      <div>
        <h3 className="font-semibold">이 공고에 맞는 크리에이터</h3>
        <p className="mt-1 text-sm text-muted-foreground">
          타겟 조건(플랫폼{campaign.target_category ? "·카테고리" : ""}
          {campaign.target_location ? "·지역" : ""})과 예산 이하 패키지 기준이에요 — 프로필에서
          문의하거나 바로 주문할 수 있습니다.
        </p>
      </div>
      <div className="grid grid-cols-2 gap-x-5 gap-y-7 md:grid-cols-4">
        {matches.map((item) => (
          <CreatorCard key={item.id} profile={item} />
        ))}
      </div>
    </div>
  );
}
