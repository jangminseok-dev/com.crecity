import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";

import CreatorCard from "@/components/creator-card";
import SortTabs from "@/components/sort-tabs";
import { Button } from "@/components/ui/button";
import { toProfileSort, type ProfileSort } from "@/lib/labels";
import { backendGet } from "@/lib/server/backend-api";
import type { ProfileListingResponse } from "@/lib/types";

const PAGE_SIZE = 20;

type PageParams = Promise<{ category: string }>;
type PageSearchParams = Promise<{ page?: string; sort?: string }>;

/** 카테고리 허브(§7-2) — 인덱싱 가능한 고유 URL. 홈 필터와 달리 쿼리 없는 정적 경로다. */
export async function generateMetadata({ params }: { params: PageParams }): Promise<Metadata> {
  const category = decodeURIComponent((await params).category);
  const title = `${category} 크리에이터 섭외 — 가격 공개 패키지`;
  const description = `${category} 분야 인플루언서·UGC 크리에이터를 찾아보세요. 가격이 공개된 패키지를 비교하고 에스크로 안전결제로 바로 협업을 시작할 수 있습니다.`;
  return {
    title,
    description,
    alternates: { canonical: `/creators/category/${encodeURIComponent(category)}` },
    openGraph: { title, description, type: "website" },
  };
}

export default async function CategoryHubPage({
  params,
  searchParams,
}: {
  params: PageParams;
  searchParams: PageSearchParams;
}) {
  const category = decodeURIComponent((await params).category);
  const { page, sort: sortParam } = await searchParams;
  const currentPage = Math.max(1, Number(page) || 1);
  const sort = toProfileSort(sortParam);

  const categories = (await backendGet<string[]>("/creator/categories")) ?? [];
  if (!categories.includes(category)) notFound();

  const query = new URLSearchParams({
    category,
    limit: String(PAGE_SIZE),
    offset: String((currentPage - 1) * PAGE_SIZE),
    ...(sort !== "latest" ? { sort } : {}),
  });
  const listing = await backendGet<ProfileListingResponse>(`/creator/profiles?${query}`);
  const items = listing?.items ?? [];
  const total = listing?.total ?? 0;
  const lastPage = Math.max(1, Math.ceil(total / PAGE_SIZE));
  const related = categories.filter((name) => name !== category);
  // 정렬은 페이지 이동·다른 카테고리로도 유지한다(홈 필터와 같은 방침)
  const hubHref = (name: string, pageNo = 1, nextSort: ProfileSort = sort) => {
    const qs = new URLSearchParams({
      ...(pageNo > 1 ? { page: String(pageNo) } : {}),
      ...(nextSort !== "latest" ? { sort: nextSort } : {}),
    }).toString();
    return `/creators/category/${encodeURIComponent(name)}${qs ? `?${qs}` : ""}`;
  };

  return (
    <div className="mx-auto max-w-6xl px-4 pb-16 pt-10 sm:px-6">
      <nav className="text-sm text-muted-foreground">
        <Link href="/" className="hover:text-foreground">
          크리에이터 찾기
        </Link>
        <span className="mx-1.5">/</span>
        <span className="font-medium text-foreground">{category}</span>
      </nav>

      <h1 className="mt-4 text-[28px] font-extrabold tracking-[-0.02em]">
        {category} 크리에이터
      </h1>
      <p className="mt-2 max-w-2xl text-[15px] text-muted-foreground">
        {category} 분야 크리에이터{total > 0 ? ` ${total}명` : ""}의 가격 공개 패키지를
        비교해 보세요. 결제 금액은 콘텐츠 승인 전까지 에스크로로 안전하게 보관됩니다.
      </p>

      {items.length === 0 ? (
        <div className="mt-10 rounded-xl border border-dashed px-6 py-14 text-center">
          <p className="text-[17px] font-semibold">아직 이 카테고리에 등록된 크리에이터가 없습니다</p>
          <p className="mt-2 text-sm text-muted-foreground">
            아래에서 다른 카테고리를 둘러보거나 전체 목록에서 찾아보세요.
          </p>
          <Link
            href="/"
            className="mt-5 inline-flex h-10 items-center justify-center rounded-md bg-primary px-5 text-sm font-semibold text-primary-foreground transition-colors hover:bg-accent-foreground"
          >
            전체 크리에이터 보기
          </Link>
        </div>
      ) : (
        <>
          <div className="mt-8 flex justify-end">
            <SortTabs current={sort} hrefFor={(next) => hubHref(category, 1, next)} />
          </div>
          <div className="mt-4 grid grid-cols-2 gap-x-5 gap-y-7 md:grid-cols-3 lg:grid-cols-4">
            {items.map((profile) => (
              <CreatorCard key={profile.id} profile={profile} />
            ))}
          </div>
        </>
      )}

      {lastPage > 1 && (
        <div className="mt-10 flex items-center justify-center gap-3">
          <Button
            variant="outline"
            size="sm"
            disabled={currentPage <= 1}
            nativeButton={false}
            render={<Link href={hubHref(category, currentPage - 1)}>이전</Link>}
          />
          <span className="text-sm text-muted-foreground">
            {currentPage} / {lastPage}
          </span>
          <Button
            variant="outline"
            size="sm"
            disabled={currentPage >= lastPage}
            nativeButton={false}
            render={<Link href={hubHref(category, currentPage + 1)}>다음</Link>}
          />
        </div>
      )}

      {/* 관련 카테고리 역링크(§7-5) — 허브끼리 내부 링크로 잇는다 */}
      {related.length > 0 && (
        <section className="mt-14 border-t pt-8">
          <h2 className="text-[15px] font-semibold">다른 카테고리 둘러보기</h2>
          <div className="mt-3.5 flex flex-wrap gap-2">
            {related.map((name) => (
              <Link
                key={name}
                href={hubHref(name)}
                className="inline-flex h-9 items-center rounded-full border bg-background px-4 text-sm text-muted-foreground transition-colors hover:text-foreground"
              >
                {name} 크리에이터
              </Link>
            ))}
          </div>
        </section>
      )}
    </div>
  );
}
