import Link from "next/link";

import { PLATFORM_LABELS, formatFollowers } from "@/lib/labels";
import { homeHref, listingQuery, type SearchFilters } from "@/lib/search-filters";
import { backendGet } from "@/lib/server/backend-api";
import type { ProfileListingResponse } from "@/lib/types";

/**
 * 빈 검색 결과 안내(갭 #48) — 막다른 길 대신 다음 행동을 준다.
 *
 * 조건을 하나씩 뺀 결과 수를 실제로 세어 **결과가 있는 완화안만** 제안한다.
 * 빈 결과일 때만 렌더되므로 평상시 추가 조회는 없다.
 */

type Relaxation = { label: string; href: string; total: number };

/** 걸린 조건 → 사람이 읽는 이름. 표시 순서가 곧 제안 순서다. */
function activeFilters(filters: SearchFilters): { key: keyof SearchFilters; label: string }[] {
  const labels: { key: keyof SearchFilters; label: string }[] = [];
  if (filters.location) labels.push({ key: "location", label: `지역 "${filters.location}"` });
  if (filters.price) labels.push({ key: "price", label: "가격대" });
  if (filters.platform) {
    const platform = PLATFORM_LABELS[filters.platform as keyof typeof PLATFORM_LABELS];
    labels.push({ key: "platform", label: platform ?? filters.platform });
  }
  if (filters.followers)
    labels.push({ key: "followers", label: `팔로워 ${formatFollowers(Number(filters.followers))}+` });
  if (filters.engagement)
    labels.push({ key: "engagement", label: `참여율 ${Number(filters.engagement) / 10}%+` });
  if (filters.category) labels.push({ key: "category", label: `${filters.category} 카테고리` });
  if (filters.q) labels.push({ key: "q", label: `검색어 "${filters.q}"` });
  return labels;
}

async function countFor(filters: SearchFilters): Promise<number> {
  const listing = await backendGet<ProfileListingResponse>(
    `/creator/profiles?${listingQuery(filters, { limit: "1" })}`
  );
  return listing?.total ?? 0;
}

export default async function EmptyResults({
  filters,
  categories,
}: {
  filters: SearchFilters;
  categories: string[];
}) {
  const active = activeFilters(filters);

  // 조건을 하나씩 빼 본다 — 결과가 나오는 것만 제안으로 남긴다
  const relaxations = (
    await Promise.all(
      active.map(async ({ key, label }): Promise<Relaxation | null> => {
        const relaxed = { ...filters, [key]: undefined };
        const total = await countFor(relaxed);
        return total > 0
          ? { label: `${label} 조건 빼기`, href: homeHref(relaxed), total }
          : null;
      })
    )
  ).filter((item): item is Relaxation => item !== null);

  const others = categories.filter((name) => name !== filters.category).slice(0, 6);

  return (
    <div className="rounded-xl border border-dashed px-6 py-12 text-center">
      <p className="text-[17px] font-semibold">조건에 맞는 크리에이터가 없습니다</p>
      {active.length > 0 && (
        <p className="mt-2 text-sm text-muted-foreground">
          걸어 둔 조건: {active.map((item) => item.label).join(" · ")}
        </p>
      )}

      {relaxations.length > 0 ? (
        <>
          <p className="mt-6 text-sm font-medium">조건을 하나 빼면 결과가 있어요</p>
          <div className="mt-3 flex flex-wrap justify-center gap-2">
            {relaxations.map((item) => (
              <Link
                key={item.href}
                href={item.href}
                className="inline-flex h-9 items-center rounded-full border bg-background px-4 text-sm transition-colors hover:border-primary"
              >
                {item.label}
                <span className="ml-1.5 text-muted-foreground">{item.total}명</span>
              </Link>
            ))}
          </div>
        </>
      ) : (
        <p className="mt-6 text-sm text-muted-foreground">
          조건을 하나만 빼도 결과가 없어요. 조건을 더 넓혀 보세요.
        </p>
      )}

      <div className="mt-7 flex flex-wrap items-center justify-center gap-2 border-t pt-6">
        <span className="text-sm text-muted-foreground">다른 카테고리 둘러보기</span>
        {others.map((name) => (
          <Link
            key={name}
            href={`/creators/category/${encodeURIComponent(name)}`}
            className="inline-flex h-8 items-center rounded-full border bg-background px-3.5 text-[13px] text-muted-foreground transition-colors hover:text-foreground"
          >
            {name}
          </Link>
        ))}
        <Link href="/" className="text-sm font-semibold text-primary hover:underline">
          전체 보기 →
        </Link>
      </div>
    </div>
  );
}
