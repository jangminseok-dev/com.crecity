import {
  Camera,
  Dumbbell,
  Home as HomeIcon,
  MessagesSquare,
  Monitor,
  PackageCheck,
  Plane,
  Search,
  Shirt,
  ShieldCheck,
  Sparkles,
  Star,
  Utensils,
  Video,
} from "lucide-react";
import Link from "next/link";
import type { ComponentType } from "react";

import CreatorCard from "@/components/creator-card";
import { Button } from "@/components/ui/button";
import { PLATFORM_LABELS } from "@/lib/labels";
import { backendGet } from "@/lib/server/backend-api";
import type { ProfileListingItem, ProfileListingResponse } from "@/lib/types";

const PAGE_SIZE = 20;

/* 가격대 프리셋 — 값은 "하한-상한"(상한 없으면 생략) 형식으로 URL에 실린다 */
const PRICE_RANGES: { value: string; label: string }[] = [
  { value: "0-100000", label: "10만원 이하" },
  { value: "100000-300000", label: "10~30만원" },
  { value: "300000-500000", label: "30~50만원" },
  { value: "500000-", label: "50만원 이상" },
];

/* 큐레이션 프리셋(§3.1) — 자주 쓰는 조합을 공유 가능한 URL 하나로 묶는다 */
const PRESETS: { label: string; query: string }[] = [
  { label: "10만원 이하 릴스", query: "platform=INSTAGRAM&price=0-100000" },
  { label: "30만원 이하 유튜브", query: "platform=YOUTUBE&price=100000-300000" },
  { label: "숏폼 전문(틱톡)", query: "platform=TIKTOK" },
  { label: "블로그 체험단", query: "platform=NAVER_BLOG" },
  { label: "서울 크리에이터", query: "location=서울" },
  { label: "프리미엄 50만원 이상", query: "price=500000-" },
];

function parsePriceRange(price?: string): { price_min?: string; price_max?: string } {
  if (!price || !/^\d+-\d*$/.test(price)) return {};
  const [min, max] = price.split("-");
  return { price_min: min, ...(max ? { price_max: max } : {}) };
}

const KEYWORDS = ["숏폼 릴스", "제품 리뷰", "브랜디드 영상", "체험단", "언박싱"];

/* 이용 흐름 4단계 — 에스크로가 핵심 차별점이라 첫 화면에서 설명한다 */
const HOW_IT_WORKS: { icon: ComponentType<{ className?: string }>; title: string; desc: string }[] =
  [
    { icon: Search, title: "크리에이터 찾기", desc: "카테고리·키워드로 검색하고 가격이 공개된 패키지를 비교해요" },
    { icon: MessagesSquare, title: "채팅으로 협의", desc: "결제 전에 궁금한 점을 직접 물어보고 조건을 맞춰요" },
    { icon: ShieldCheck, title: "에스크로 결제", desc: "결제 금액은 콘텐츠 승인 전까지 크리시티가 안전하게 보관해요" },
    { icon: PackageCheck, title: "콘텐츠 수령", desc: "결과물을 확인하고 승인하면 크리에이터에게 정산돼요" },
  ];

const CATEGORY_ICONS: Record<string, ComponentType<{ className?: string }>> = {
  뷰티: Sparkles,
  패션: Shirt,
  푸드: Utensils,
  여행: Plane,
  테크: Monitor,
  피트니스: Dumbbell,
  라이프: HomeIcon,
  포토: Camera,
  영상: Video,
};

type HomeSearchParams = Promise<{
  category?: string;
  q?: string;
  page?: string;
  platform?: string;
  price?: string;
  location?: string;
}>;

export default async function Home({ searchParams }: { searchParams: HomeSearchParams }) {
  const { category, q, page, platform, price, location } = await searchParams;
  const currentPage = Math.max(1, Number(page) || 1);
  const query = new URLSearchParams({
    limit: String(PAGE_SIZE),
    offset: String((currentPage - 1) * PAGE_SIZE),
    ...(category ? { category } : {}),
    ...(q ? { q } : {}),
    ...(platform ? { platform } : {}),
    ...parsePriceRange(price),
    ...(location ? { location } : {}),
  });
  const isFiltered = Boolean(category || q || platform || price || location || currentPage > 1);
  const [listing, categories, popular] = await Promise.all([
    backendGet<ProfileListingResponse>(`/creator/profiles?${query}`),
    backendGet<string[]>("/creator/categories"),
    // 인기 섹션은 필터 없는 첫 화면에서만 보여준다
    isFiltered ? Promise.resolve(null) : backendGet<ProfileListingItem[]>("/creator/profiles/popular?limit=4"),
  ]);
  const items = listing?.items ?? [];
  const total = listing?.total ?? 0;
  const lastPage = Math.max(1, Math.ceil(total / PAGE_SIZE));

  const filterHref = (params: { category?: string; q?: string; page?: number }) => {
    const merged = new URLSearchParams({
      ...(params.category ? { category: params.category } : {}),
      ...(params.q ? { q: params.q } : {}),
      // 상세 필터(플랫폼·가격대·위치)는 카테고리·페이지 이동에도 유지한다
      ...(platform ? { platform } : {}),
      ...(price ? { price } : {}),
      ...(location ? { location } : {}),
      ...((params.page ?? 1) > 1 ? { page: String(params.page) } : {}),
    });
    const qs = merged.toString();
    return qs ? `/?${qs}` : "/";
  };

  return (
    <div>
      {/* 히어로 — 큰 헤드라인 + 필 검색바 + 인기 키워드 칩 */}
      <section className="border-b border-secondary bg-linear-to-b from-[#f9fafb] to-background">
        <div className="mx-auto flex max-w-6xl flex-col items-center px-4 pb-11 pt-14 text-center sm:px-6">
          <h1 className="text-3xl font-extrabold leading-[1.3] tracking-[-0.03em] sm:text-4xl">
            브랜드에 딱 맞는
            <br />
            크리에이터를 찾아보세요
          </h1>
          <p className="mt-3 text-[17px] text-muted-foreground">
            탐색부터 협의·에스크로 결제까지, 캠페인을 한 곳에서 진행해요
          </p>
          {/* 검색 — GET 폼이라 상태 없이 URL로 수렴한다 */}
          <form
            action="/"
            method="get"
            className="mt-7 flex h-15 w-full max-w-[620px] items-center gap-3 rounded-full border-[1.5px] bg-background pl-6 pr-3 shadow-raised"
          >
            <Search className="size-5 shrink-0 text-muted-foreground" />
            <input
              name="q"
              defaultValue={q ?? ""}
              placeholder="어떤 크리에이터가 필요하세요?"
              className="min-w-0 flex-1 bg-transparent text-[17px] outline-none placeholder:text-muted-foreground/70"
            />
            {category && <input type="hidden" name="category" value={category} />}
            <button
              type="submit"
              className="h-11 shrink-0 rounded-full bg-primary px-5.5 text-[15px] font-semibold text-primary-foreground transition-colors hover:bg-accent-foreground"
            >
              검색
            </button>
          </form>
          <div className="mt-4 flex flex-wrap justify-center gap-2">
            {KEYWORDS.map((keyword) => (
              <Link
                key={keyword}
                href={`/?q=${encodeURIComponent(keyword)}`}
                className="inline-flex h-8 items-center rounded-full border bg-background px-3.5 text-[13px] text-muted-foreground transition-colors hover:text-foreground"
              >
                {keyword}
              </Link>
            ))}
          </div>
        </div>
      </section>

      <div className="mx-auto max-w-6xl px-4 pb-16 sm:px-6">
        {/* 카테고리 아이콘 행 */}
        {categories && categories.length > 0 && (
          <div className="flex flex-wrap justify-center gap-x-5 gap-y-5 pt-9 sm:gap-x-9">
            {categories.map((name) => {
              const Icon = CATEGORY_ICONS[name] ?? Star;
              const active = category === name;
              return (
                <Link
                  key={name}
                  href={filterHref({ category: active ? undefined : name, q })}
                  className="flex flex-col items-center gap-2"
                >
                  <span
                    className={`inline-flex size-[58px] items-center justify-center rounded-full transition-colors ${
                      active
                        ? "bg-primary text-primary-foreground"
                        : "bg-secondary text-foreground/70"
                    }`}
                  >
                    <Icon className="size-6" />
                  </span>
                  <span
                    className={`text-[13px] ${
                      active ? "font-bold text-primary" : "font-medium text-foreground/70"
                    }`}
                  >
                    {name}
                  </span>
                </Link>
              );
            })}
          </div>
        )}

        {/* 이번 주 인기 크리에이터 — 최근 7일 주문 수 기준 */}
        {popular && popular.length > 0 && (
          <section>
            <div className="mb-6 mt-14">
              <h2 className="text-[22px] font-bold tracking-[-0.02em]">이번 주 인기 크리에이터</h2>
              <p className="mt-1 text-sm text-muted-foreground">
                지난 7일 동안 브랜드가 가장 많이 찾았어요
              </p>
            </div>
            <div className="grid grid-cols-2 gap-x-5 gap-y-7 md:grid-cols-3 lg:grid-cols-4">
              {popular.map((profile) => (
                <CreatorCard key={profile.id} profile={profile} />
              ))}
            </div>
          </section>
        )}

        {/* 큐레이션 프리셋 — 필터 조합 바로가기(공유 가능한 URL) */}
        <div className="mt-12 flex flex-wrap items-center gap-2">
          <span className="text-sm font-semibold">이런 조합은 어때요?</span>
          {PRESETS.map((preset) => (
            <Link
              key={preset.label}
              href={`/?${preset.query}`}
              className="inline-flex h-8 items-center rounded-full border bg-background px-3.5 text-[13px] text-muted-foreground transition-colors hover:border-primary hover:text-foreground"
            >
              {preset.label}
            </Link>
          ))}
        </div>

        {/* 검색 필터 확장 — 플랫폼·가격대·위치 (§3.1, GET 폼이라 상태 없이 URL로 수렴) */}
        <form
          action="/"
          method="get"
          className="mt-3 flex flex-wrap items-center gap-2 rounded-2xl border bg-card p-3"
        >
          {q && <input type="hidden" name="q" value={q} />}
          {category && <input type="hidden" name="category" value={category} />}
          <select
            name="platform"
            defaultValue={platform ?? ""}
            className="h-10 rounded-lg border border-input bg-transparent px-3 text-sm"
          >
            <option value="">플랫폼 전체</option>
            {Object.entries(PLATFORM_LABELS).map(([value, label]) => (
              <option key={value} value={value}>
                {label}
              </option>
            ))}
          </select>
          <select
            name="price"
            defaultValue={price ?? ""}
            className="h-10 rounded-lg border border-input bg-transparent px-3 text-sm"
          >
            <option value="">가격대 전체</option>
            {PRICE_RANGES.map((range) => (
              <option key={range.value} value={range.value}>
                {range.label}
              </option>
            ))}
          </select>
          <input
            name="location"
            defaultValue={location ?? ""}
            placeholder="지역 (예: 서울)"
            className="h-10 w-36 rounded-lg border border-input bg-transparent px-3 text-sm outline-none focus:border-primary"
          />
          <button
            type="submit"
            className="h-10 rounded-lg bg-primary px-4 text-sm font-semibold text-primary-foreground transition-colors hover:bg-accent-foreground"
          >
            필터 적용
          </button>
          {(platform || price || location) && (
            <Link
              href={category || q ? `/?${new URLSearchParams({ ...(category ? { category } : {}), ...(q ? { q } : {}) })}` : "/"}
              className="px-2 text-sm font-medium text-muted-foreground hover:text-foreground"
            >
              필터 초기화 ✕
            </Link>
          )}
        </form>

        {/* 섹션 헤더 */}
        <section>
          <div className="mb-6 mt-14 flex items-end justify-between">
            <div>
              <h2 className="text-[22px] font-bold tracking-[-0.02em]">
                {q ? `"${q}" 검색 결과` : category ? `${category} 크리에이터` : "전체 크리에이터"}
              </h2>
              <p className="mt-1 text-sm text-muted-foreground">
                {total > 0 ? `${total}명의 크리에이터` : "크리에이터"} · 프로필 심사를 거쳐 등록됩니다
              </p>
            </div>
            {q && (
              <Link
                href={filterHref({ category })}
                className="text-sm font-semibold text-primary hover:underline"
              >
                검색 해제 ✕
              </Link>
            )}
          </div>

          {items.length === 0 ? (
            <p className="rounded-xl border border-dashed py-16 text-center text-muted-foreground">
              {isFiltered
                ? "조건에 맞는 크리에이터가 없습니다."
                : "아직 등록된 크리에이터가 없습니다."}
            </p>
          ) : (
            <div className="grid grid-cols-2 gap-x-5 gap-y-7 md:grid-cols-3 lg:grid-cols-4">
              {items.map((profile) => (
                <CreatorCard key={profile.id} profile={profile} />
              ))}
            </div>
          )}

          {lastPage > 1 && (
            <div className="mt-10 flex items-center justify-center gap-3">
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

        {/* 이용 흐름 4단계 */}
        <section className="mt-20">
          <h2 className="text-center text-[22px] font-bold tracking-[-0.02em]">
            쉽고 안전한 캠페인 진행
          </h2>
          <p className="mt-1.5 text-center text-sm text-muted-foreground">
            탐색부터 정산까지, crecity가 중간에서 안전하게 진행해요
          </p>
          <div className="mt-10 grid gap-x-6 gap-y-8 sm:grid-cols-2 lg:grid-cols-4">
            {HOW_IT_WORKS.map((step, index) => (
              <div key={step.title} className="flex flex-col items-center text-center">
                <span className="inline-flex size-14 items-center justify-center rounded-2xl bg-accent text-accent-foreground">
                  <step.icon className="size-6" />
                </span>
                <p className="mt-4 text-[15px] font-semibold">
                  <span className="mr-1.5 text-muted-foreground/60">{index + 1}</span>
                  {step.title}
                </p>
                <p className="mt-1.5 max-w-[240px] text-[13px] leading-relaxed text-muted-foreground">
                  {step.desc}
                </p>
              </div>
            ))}
          </div>
        </section>
      </div>
    </div>
  );
}
