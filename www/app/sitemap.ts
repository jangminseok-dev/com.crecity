import type { MetadataRoute } from "next";

import { backendGet } from "@/lib/server/backend-api";
import { SITE_URL } from "@/lib/site";
import type { ProfileListingResponse } from "@/lib/types";

const PAGE_SIZE = 50; // 백엔드 목록 limit 상한

/** 프로그래매틱 SEO의 핵심 — 승인된 크리에이터 프로필 전부를 사이트맵에 올린다. */
export default async function sitemap(): Promise<MetadataRoute.Sitemap> {
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
    ...profiles,
  ];
}
