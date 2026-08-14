import type { MetadataRoute } from "next";

import { PERSONAS } from "@/lib/personas";
import { backendGet } from "@/lib/server/backend-api";
import { SITE_URL } from "@/lib/site";
import type { ProfileListingResponse } from "@/lib/types";

const PAGE_SIZE = 50; // 백엔드 목록 limit 상한

/** 프로그래매틱 SEO의 핵심 — 승인된 프로필 전부 + 카테고리 허브를 사이트맵에 올린다. */
export default async function sitemap(): Promise<MetadataRoute.Sitemap> {
  const categories = (await backendGet<string[]>("/creator/categories")) ?? [];
  const categoryHubs: MetadataRoute.Sitemap = categories.map((name) => ({
    url: `${SITE_URL}/creators/category/${encodeURIComponent(name)}`,
    changeFrequency: "daily" as const,
    priority: 0.9, // 허브는 프로필보다 상위 인덱싱 대상(§7-2)
  }));

  const profiles: MetadataRoute.Sitemap = [];
  for (let offset = 0; ; offset += PAGE_SIZE) {
    const listing = await backendGet<ProfileListingResponse>(
      `/creator/profiles?limit=${PAGE_SIZE}&offset=${offset}`,
    );
    if (!listing) break;
    profiles.push(
      ...listing.items.map((item) => ({
        url: `${SITE_URL}/creators/${item.slug}`,
        lastModified: item.created_at ?? undefined,
        changeFrequency: "weekly" as const,
        priority: 0.8,
      })),
    );
    if (offset + PAGE_SIZE >= listing.total) break;
  }

  return [
    { url: SITE_URL, changeFrequency: "daily", priority: 1 },
    ...categoryHubs,
    ...profiles,
    // 페르소나 랜딩(§5) — 카테고리 허브와 함께 상위 인덱싱 대상
    ...PERSONAS.map((persona) => ({
      url: `${SITE_URL}/for/${persona.slug}`,
      changeFrequency: "monthly" as const,
      priority: 0.8,
    })),
    // 이용 방법(§2.1-11) — 신뢰 장치 겸 롱테일 랜딩
    { url: `${SITE_URL}/how-it-works`, changeFrequency: "monthly", priority: 0.8 },
    // 무료 도구(§3.9) — 검색 유입용 리드 마그넷
    { url: `${SITE_URL}/tools`, changeFrequency: "monthly", priority: 0.7 },
    { url: `${SITE_URL}/tools/pricing-calculator`, changeFrequency: "monthly", priority: 0.7 },
    { url: `${SITE_URL}/tools/engagement-calculator`, changeFrequency: "monthly", priority: 0.7 },
    { url: `${SITE_URL}/tools/campaign-brief`, changeFrequency: "monthly", priority: 0.7 },
    { url: `${SITE_URL}/terms`, changeFrequency: "yearly", priority: 0.3 },
    { url: `${SITE_URL}/privacy`, changeFrequency: "yearly", priority: 0.3 },
  ];
}
