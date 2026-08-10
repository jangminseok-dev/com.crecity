import Link from "next/link";

import CreatorCard from "@/components/creator-card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { backendGet } from "@/lib/server/backend-api";
import type { ProfileListingResponse } from "@/lib/types";

const PAGE_SIZE = 20;

type HomeSearchParams = Promise<{ category?: string; page?: string }>;

export default async function Home({ searchParams }: { searchParams: HomeSearchParams }) {
  const { category, page } = await searchParams;
  const currentPage = Math.max(1, Number(page) || 1);
  const query = new URLSearchParams({
    limit: String(PAGE_SIZE),
    offset: String((currentPage - 1) * PAGE_SIZE),
    ...(category ? { category } : {}),
  });
  const listing = await backendGet<ProfileListingResponse>(`/creator/profiles?${query}`);
  const items = listing?.items ?? [];
  const total = listing?.total ?? 0;
  const lastPage = Math.max(1, Math.ceil(total / PAGE_SIZE));

  const pageHref = (target: number) => {
    const params = new URLSearchParams({
      ...(category ? { category } : {}),
      ...(target > 1 ? { page: String(target) } : {}),
    });
    const qs = params.toString();
    return qs ? `/?${qs}` : "/";
  };

  return (
    <div className="mx-auto max-w-5xl px-4 py-10">
      <section className="py-8 text-center">
        <h1 className="text-3xl font-bold tracking-tight sm:text-4xl">
          우리 브랜드에 맞는 크리에이터를 찾아보세요
        </h1>
        <p className="mt-3 text-muted-foreground">
          인스타그램 · 유튜브 · 틱톡 · 네이버 블로그 · UGC — 가격이 공개된 패키지로 바로
          주문까지
        </p>
      </section>

      <section className="mt-6">
        <div className="mb-4 flex items-center justify-between">
          <h2 className="text-lg font-semibold">
            크리에이터 {total > 0 && <span className="text-muted-foreground">({total})</span>}
          </h2>
          {category && (
            <Link href="/">
              <Badge variant="outline">카테고리: {category} ✕</Badge>
            </Link>
          )}
        </div>

        {items.length === 0 ? (
          <p className="rounded-lg border border-dashed py-16 text-center text-muted-foreground">
            아직 등록된 크리에이터가 없습니다.
          </p>
        ) : (
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {items.map((profile) => (
              <CreatorCard key={profile.id} profile={profile} />
            ))}
          </div>
        )}

        {lastPage > 1 && (
          <div className="mt-8 flex items-center justify-center gap-3">
            <Button
              variant="outline"
              size="sm"
              disabled={currentPage <= 1}
              nativeButton={false} render={<Link href={pageHref(currentPage - 1)}>이전</Link>}
            />
            <span className="text-sm text-muted-foreground">
              {currentPage} / {lastPage}
            </span>
            <Button
              variant="outline"
              size="sm"
              disabled={currentPage >= lastPage}
              nativeButton={false} render={<Link href={pageHref(currentPage + 1)}>다음</Link>}
            />
          </div>
        )}
      </section>
    </div>
  );
}
