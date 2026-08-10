import Link from "next/link";

import CreatorCard from "@/components/creator-card";
import { Badge } from "@/components/ui/badge";
import { Button, buttonVariants } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { backendGet } from "@/lib/server/backend-api";
import type { ProfileListingResponse } from "@/lib/types";

const PAGE_SIZE = 20;

type HomeSearchParams = Promise<{ category?: string; q?: string; page?: string }>;

export default async function Home({ searchParams }: { searchParams: HomeSearchParams }) {
  const { category, q, page } = await searchParams;
  const currentPage = Math.max(1, Number(page) || 1);
  const query = new URLSearchParams({
    limit: String(PAGE_SIZE),
    offset: String((currentPage - 1) * PAGE_SIZE),
    ...(category ? { category } : {}),
    ...(q ? { q } : {}),
  });
  const [listing, categories] = await Promise.all([
    backendGet<ProfileListingResponse>(`/creator/profiles?${query}`),
    backendGet<string[]>("/creator/categories"),
  ]);
  const items = listing?.items ?? [];
  const total = listing?.total ?? 0;
  const lastPage = Math.max(1, Math.ceil(total / PAGE_SIZE));

  const filterHref = (params: { category?: string; q?: string; page?: number }) => {
    const merged = new URLSearchParams({
      ...(params.category ? { category: params.category } : {}),
      ...(params.q ? { q: params.q } : {}),
      ...((params.page ?? 1) > 1 ? { page: String(params.page) } : {}),
    });
    const qs = merged.toString();
    return qs ? `/?${qs}` : "/";
  };

  return (
    <div className="mx-auto max-w-5xl px-4 py-10">
      <section className="rounded-2xl bg-muted/60 px-6 py-12 text-center">
        <h1 className="text-3xl font-bold tracking-tight sm:text-4xl">
          우리 브랜드에 맞는 크리에이터를 찾아보세요
        </h1>
        <p className="mt-3 text-muted-foreground">
          인스타그램 · 유튜브 · 틱톡 · 네이버 블로그 · UGC — 가격이 공개된 패키지로 바로
          주문까지
        </p>
        {/* 검색 — GET 폼이라 상태 없이 URL로 수렴한다 */}
        <form action="/" method="get" className="mx-auto mt-6 flex max-w-md gap-2">
          <Input
            name="q"
            defaultValue={q ?? ""}
            placeholder="크리에이터 이름·소개 검색"
            className="bg-background"
          />
          {category && <input type="hidden" name="category" value={category} />}
          <Button type="submit">검색</Button>
        </form>
      </section>

      {/* 카테고리 필터 칩 */}
      {categories && categories.length > 0 && (
        <div className="mt-6 flex flex-wrap items-center gap-2">
          <Link
            href={filterHref({ q })}
            className={buttonVariants({ variant: category ? "outline" : "default", size: "sm" })}
          >
            전체
          </Link>
          {categories.map((name) => (
            <Link
              key={name}
              href={filterHref({ category: name, q })}
              className={buttonVariants({
                variant: category === name ? "default" : "outline",
                size: "sm",
              })}
            >
              {name}
            </Link>
          ))}
        </div>
      )}

      <section className="mt-6">
        <div className="mb-4 flex items-center justify-between">
          <h2 className="text-lg font-semibold">
            {q ? `"${q}" 검색 결과` : "크리에이터"}{" "}
            {total > 0 && <span className="text-muted-foreground">({total})</span>}
          </h2>
          {q && (
            <Link href={filterHref({ category })}>
              <Badge variant="outline">검색 해제 ✕</Badge>
            </Link>
          )}
        </div>

        {items.length === 0 ? (
          <p className="rounded-lg border border-dashed py-16 text-center text-muted-foreground">
            {q || category ? "조건에 맞는 크리에이터가 없습니다." : "아직 등록된 크리에이터가 없습니다."}
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
              nativeButton={false}
              render={<Link href={filterHref({ category, q, page: currentPage - 1 })}>이전</Link>}
            />
            <span className="text-sm text-muted-foreground">
              {currentPage} / {lastPage}
            </span>
            <Button
              variant="outline"
              size="sm"
              disabled={currentPage >= lastPage}
              nativeButton={false}
              render={<Link href={filterHref({ category, q, page: currentPage + 1 })}>다음</Link>}
            />
          </div>
        )}
      </section>
    </div>
  );
}
