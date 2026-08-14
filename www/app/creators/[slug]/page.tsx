import { ArrowLeft, Star } from "lucide-react";
import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";

import CreatorAnalyticsSection from "@/components/creator-analytics-section";
import CreatorReviews from "@/components/creator-reviews";
import PackagePicker from "@/components/package-picker";
import PortfolioGallery from "@/components/portfolio-gallery";
import ProfileFaqAccordion from "@/components/profile-faq";
import ProfileViewTracker from "@/components/profile-view-tracker";
import ReportButton from "@/components/report-button";
import { Badge } from "@/components/ui/badge";
import { PLATFORM_LABELS, formatFollowers } from "@/lib/labels";
import { backendGet } from "@/lib/server/backend-api";
import type { CreatorPackage, CreatorProfile, PortfolioItem, ProfileFaq } from "@/lib/types";

/* 프로필 사진이 없을 때 이니셜 뒤에 깔리는 틴트 — creator-card와 동일 */
const TINTS: [string, string][] = [
  ["#f2f4f6", "#e5e8eb"],
  ["#eef0f3", "#dde1e6"],
  ["#f4f3f1", "#e8e6e2"],
  ["#eef1f5", "#dfe4ea"],
  ["#f0f2f4", "#e2e6ea"],
];

type PageParams = Promise<{ slug: string }>;

/* 헤더 평점 요약용 — 집계는 비로그인에도 공개(리뷰 블러 정책과 무관) */
type ReviewSummary = { total: number; average_overall: number | null };

async function fetchProfile(slug: string) {
  return backendGet<CreatorProfile>(`/creator/profiles/${encodeURIComponent(slug)}`);
}

export async function generateMetadata({ params }: { params: PageParams }): Promise<Metadata> {
  const { slug } = await params;
  const profile = await fetchProfile(slug);
  if (!profile) return { title: "크리에이터를 찾을 수 없습니다 — crecity" };
  const title = `${profile.name} — ${profile.primary_category} 크리에이터`;
  const description = profile.tagline || profile.bio.slice(0, 120);
  return {
    title,
    description,
    alternates: { canonical: `/creators/${encodeURIComponent(slug)}` },
    openGraph: { title, description, type: "profile" },
  };
}

export default async function CreatorProfilePage({ params }: { params: PageParams }) {
  const { slug } = await params;
  const [profile, packages, portfolio, reviews, faqs] = await Promise.all([
    fetchProfile(slug),
    backendGet<CreatorPackage[]>(`/creator/profiles/${encodeURIComponent(slug)}/packages`),
    backendGet<PortfolioItem[]>(`/creator/profiles/${encodeURIComponent(slug)}/portfolio`),
    backendGet<ReviewSummary>(`/review/creators/${encodeURIComponent(slug)}`),
    backendGet<ProfileFaq[]>(`/creator/profiles/${encodeURIComponent(slug)}/faqs`),
  ]);
  if (!profile) notFound();

  const photos = portfolio ?? [];
  const cover = photos[0];
  const [tintFrom, tintTo] = TINTS[profile.name.charCodeAt(0) % TINTS.length];
  const platforms = [...new Set((packages ?? []).map((pkg) => pkg.platform))];

  return (
    <div className="mx-auto max-w-6xl px-4 pb-20 pt-7 sm:px-6">
      <ProfileViewTracker slug={profile.slug} />
      <Link
        href="/"
        className="mb-5 inline-flex items-center gap-1.5 text-sm text-muted-foreground transition-colors hover:text-foreground"
      >
        <ArrowLeft className="size-4" />
        크리에이터 찾기
      </Link>

      <div className="grid items-start gap-12 lg:grid-cols-[1fr_360px]">
        <div>
          {/* 프로필 헤더 */}
          <section className="mb-7 flex flex-col gap-6 sm:flex-row sm:items-start">
            <div className="w-[180px] shrink-0 overflow-hidden rounded-xl">
              {cover ? (
                // eslint-disable-next-line @next/next/no-img-element
                <img
                  src={`/api/backend${cover.image_url}`}
                  alt={`${profile.name} 프로필`}
                  className="aspect-[4/5] w-full object-cover"
                />
              ) : (
                <div
                  className="flex aspect-[4/5] w-full items-center justify-center text-[40px] font-bold text-foreground/25"
                  style={{ background: `linear-gradient(160deg, ${tintFrom}, ${tintTo})` }}
                >
                  {profile.name.slice(0, 1)}
                </div>
              )}
            </div>
            <div className="flex-1 pt-1.5">
              <div className="flex flex-wrap items-center gap-2">
                <h1 className="text-[26px] font-bold tracking-[-0.02em]">{profile.name}</h1>
                {profile.followers_total > 0 && (
                  <Badge variant="secondary">
                    팔로워 {formatFollowers(profile.followers_total)}
                  </Badge>
                )}
                {profile.status !== "APPROVED" && <Badge variant="outline">심사 대기 중</Badge>}
                {!profile.accepting_orders && (
                  <Badge variant="outline">지금은 주문을 받지 않아요</Badge>
                )}
              </div>
              <p className="mt-2 text-[15px] text-muted-foreground">
                {profile.primary_category}
                {profile.location ? ` · ${profile.location}` : ""}
              </p>
              <p className="mt-1 text-[15px] text-muted-foreground">{profile.tagline}</p>
              {reviews && reviews.total > 0 && reviews.average_overall !== null && (
                <p className="mt-2.5 inline-flex items-center gap-1 text-[15px] font-semibold">
                  <Star className="size-4 fill-foreground text-foreground" />
                  {reviews.average_overall.toFixed(1)}
                  <span className="ml-0.5 font-normal text-muted-foreground">
                    리뷰 {reviews.total}
                  </span>
                </p>
              )}
              <div className="mt-3.5 flex flex-wrap gap-1.5">
                {/* 카테고리 칩은 허브 페이지 역링크(§7-5) — 내부 링크로 인덱싱을 잇는다 */}
                <Link
                  href={`/creators/category/${encodeURIComponent(profile.primary_category)}`}
                  className="inline-flex h-7 items-center rounded-full bg-secondary px-3 text-[13px] text-secondary-foreground transition-colors hover:bg-accent"
                >
                  {profile.primary_category} 크리에이터
                </Link>
                {platforms.map((p) => (
                  <span
                    key={p}
                    className="inline-flex h-7 items-center rounded-full bg-secondary px-3 text-[13px] text-secondary-foreground"
                  >
                    {PLATFORM_LABELS[p]}
                  </span>
                ))}
              </div>
              <p className="mt-4 whitespace-pre-line text-[15px] leading-relaxed">{profile.bio}</p>
            </div>
          </section>

          {/* 포트폴리오 갤러리 */}
          {photos.length > 0 && (
            <section className="mt-10">
              <h2 className="border-b pb-3 text-[15px] font-semibold">
                포트폴리오 <span className="ml-1 font-normal text-muted-foreground">{photos.length}</span>
              </h2>
              <div className="mt-5">
                <PortfolioGallery photos={photos} name={profile.name} />
              </div>
            </section>
          )}

          {/* FAQ 아코디언(§2.1-9) — 크리에이터가 직접 쓴 Q&A */}
          {faqs && faqs.length > 0 && (
            <section className="mt-10">
              <h2 className="border-b pb-3 text-[15px] font-semibold">자주 묻는 질문</h2>
              <div className="mt-5">
                <ProfileFaqAccordion faqs={faqs} />
              </div>
            </section>
          )}

          {/* 채널 분석 — 자가입력+스크린샷 인증, 비로그인은 가입 게이트(§9.2) */}
          <section className="mt-10">
            <h2 className="border-b pb-3 text-[15px] font-semibold">채널 분석</h2>
            <div className="mt-5">
              <CreatorAnalyticsSection slug={profile.slug} />
            </div>
          </section>

          {/* 리뷰 — 집계 공개, 원문은 로그인 시(블러 정책) */}
          <section className="mt-10">
            <h2 className="border-b pb-3 text-[15px] font-semibold">리뷰</h2>
            <div className="mt-5">
              <CreatorReviews slug={profile.slug} />
            </div>
          </section>

          {/* 부적절한 프로필 신고(갭 #54) — 로그인 사용자에게만 보인다 */}
          <div className="mt-10 border-t pt-5">
            <ReportButton
              targetType="PROFILE"
              targetId={profile.id}
              label="이 프로필 신고하기"
            />
          </div>
        </div>

        <PackagePicker
          acceptingOrders={profile.accepting_orders}
          slug={profile.slug}
          packages={packages ?? []}
          shortlistItem={{
            slug: profile.slug,
            name: profile.name,
            primary_category: profile.primary_category,
            tagline: profile.tagline,
            location: profile.location,
            cover_image_url: cover?.image_url ?? null,
            price_from: packages?.[0]?.price_krw ?? null, // 목록은 가격 오름차순
            rating_avg: reviews?.average_overall ?? null,
            rating_count: reviews?.total ?? 0,
          }}
        />
      </div>
    </div>
  );
}
