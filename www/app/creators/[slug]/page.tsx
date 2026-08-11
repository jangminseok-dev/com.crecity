import { ArrowLeft } from "lucide-react";
import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";

import CreatorReviews from "@/components/creator-reviews";
import PackagePicker from "@/components/package-picker";
import { Badge } from "@/components/ui/badge";
import { PLATFORM_LABELS } from "@/lib/labels";
import { backendGet } from "@/lib/server/backend-api";
import type { CreatorPackage, CreatorProfile, PortfolioItem } from "@/lib/types";

/* 프로필 사진이 없을 때 이니셜 뒤에 깔리는 틴트 — creator-card와 동일 */
const TINTS: [string, string][] = [
  ["#f2f4f6", "#e5e8eb"],
  ["#eef0f3", "#dde1e6"],
  ["#f4f3f1", "#e8e6e2"],
  ["#eef1f5", "#dfe4ea"],
  ["#f0f2f4", "#e2e6ea"],
];

type PageParams = Promise<{ slug: string }>;

async function fetchProfile(slug: string) {
  return backendGet<CreatorProfile>(`/creator/profiles/${encodeURIComponent(slug)}`);
}

export async function generateMetadata({ params }: { params: PageParams }): Promise<Metadata> {
  const { slug } = await params;
  const profile = await fetchProfile(slug);
  if (!profile) return { title: "크리에이터를 찾을 수 없습니다 — crecity" };
  const title = `${profile.name} — ${profile.primary_category} 크리에이터 | crecity`;
  const description = profile.tagline || profile.bio.slice(0, 120);
  return {
    title,
    description,
    openGraph: { title, description, type: "profile" },
  };
}

export default async function CreatorProfilePage({ params }: { params: PageParams }) {
  const { slug } = await params;
  const [profile, packages, portfolio] = await Promise.all([
    fetchProfile(slug),
    backendGet<CreatorPackage[]>(`/creator/profiles/${encodeURIComponent(slug)}/packages`),
    backendGet<PortfolioItem[]>(`/creator/profiles/${encodeURIComponent(slug)}/portfolio`),
  ]);
  if (!profile) notFound();

  const photos = portfolio ?? [];
  const cover = photos[0];
  const [tintFrom, tintTo] = TINTS[profile.name.charCodeAt(0) % TINTS.length];
  const platforms = [...new Set((packages ?? []).map((pkg) => pkg.platform))];

  return (
    <div className="mx-auto max-w-6xl px-4 pb-20 pt-7 sm:px-6">
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
                {profile.status !== "APPROVED" && <Badge variant="outline">심사 대기 중</Badge>}
              </div>
              <p className="mt-2 text-[15px] text-muted-foreground">
                {profile.primary_category}
                {profile.location ? ` · ${profile.location}` : ""}
              </p>
              <p className="mt-1 text-[15px] text-muted-foreground">{profile.tagline}</p>
              <div className="mt-3.5 flex flex-wrap gap-1.5">
                {[profile.primary_category, ...platforms.map((p) => PLATFORM_LABELS[p])].map(
                  (tag) => (
                    <span
                      key={tag}
                      className="inline-flex h-7 items-center rounded-full bg-secondary px-3 text-[13px] text-secondary-foreground"
                    >
                      {tag}
                    </span>
                  ),
                )}
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
              <div className="mt-5 grid grid-cols-2 gap-4 sm:grid-cols-3">
                {photos.map((item) => (
                  <div key={item.id} className="aspect-square overflow-hidden rounded-xl">
                    {/* eslint-disable-next-line @next/next/no-img-element */}
                    <img
                      src={`/api/backend${item.image_url}`}
                      alt={`${profile.name} 포트폴리오`}
                      className="size-full object-cover transition-transform duration-200 hover:scale-[1.03]"
                    />
                  </div>
                ))}
              </div>
            </section>
          )}

          {/* 리뷰 — 집계 공개, 원문은 로그인 시(블러 정책) */}
          <section className="mt-10">
            <h2 className="border-b pb-3 text-[15px] font-semibold">리뷰</h2>
            <div className="mt-5">
              <CreatorReviews slug={profile.slug} />
            </div>
          </section>
        </div>

        <PackagePicker slug={profile.slug} packages={packages ?? []} />
      </div>
    </div>
  );
}
