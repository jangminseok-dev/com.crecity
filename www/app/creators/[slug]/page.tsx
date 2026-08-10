import type { Metadata } from "next";
import { notFound } from "next/navigation";

import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Separator } from "@/components/ui/separator";
import { PLATFORM_LABELS, formatKrw } from "@/lib/labels";
import { backendGet } from "@/lib/server/backend-api";
import type { CreatorPackage, CreatorProfile } from "@/lib/types";

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
  const [profile, packages] = await Promise.all([
    fetchProfile(slug),
    backendGet<CreatorPackage[]>(`/creator/profiles/${encodeURIComponent(slug)}/packages`),
  ]);
  if (!profile) notFound();

  return (
    <div className="mx-auto max-w-5xl px-4 py-10">
      {/* 프로필 헤더 */}
      <section className="flex flex-col gap-4 sm:flex-row sm:items-center">
        <div className="flex size-20 shrink-0 items-center justify-center rounded-full bg-muted text-3xl font-bold">
          {profile.name.slice(0, 1)}
        </div>
        <div className="flex-1">
          <div className="flex flex-wrap items-center gap-2">
            <h1 className="text-2xl font-bold">{profile.name}</h1>
            <Badge variant="secondary">{profile.primary_category}</Badge>
            {profile.status !== "APPROVED" && <Badge variant="outline">심사 대기 중</Badge>}
          </div>
          <p className="mt-1 text-muted-foreground">{profile.tagline}</p>
          {profile.location && (
            <p className="mt-1 text-sm text-muted-foreground">📍 {profile.location}</p>
          )}
        </div>
      </section>

      <Separator className="my-8" />

      {/* 소개 */}
      <section>
        <h2 className="mb-3 text-lg font-semibold">소개</h2>
        <p className="whitespace-pre-line leading-relaxed text-foreground/90">{profile.bio}</p>
      </section>

      {/* 패키지 가격표 */}
      <section className="mt-10">
        <h2 className="mb-4 text-lg font-semibold">판매 패키지</h2>
        {!packages || packages.length === 0 ? (
          <p className="rounded-lg border border-dashed py-10 text-center text-muted-foreground">
            아직 등록된 패키지가 없습니다.
          </p>
        ) : (
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
            {packages.map((pkg) => (
              <Card key={pkg.id}>
                <CardHeader>
                  <div className="flex items-center justify-between gap-2">
                    <CardTitle className="text-base">{pkg.title}</CardTitle>
                    <Badge variant="outline">{PLATFORM_LABELS[pkg.platform]}</Badge>
                  </div>
                </CardHeader>
                <CardContent className="flex flex-col gap-3">
                  <p className="text-sm text-muted-foreground">{pkg.description}</p>
                  <p className="text-xl font-bold">{formatKrw(pkg.price_krw)}</p>
                </CardContent>
              </Card>
            ))}
          </div>
        )}
      </section>
    </div>
  );
}
