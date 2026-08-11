import { Star } from "lucide-react";
import Link from "next/link";

import { formatKrw } from "@/lib/labels";
import type { ProfileListingItem } from "@/lib/types";

/* 프로필 사진이 없을 때 이니셜 뒤에 깔리는 틴트 — 디자인 시스템 CreatorCard와 동일 */
const TINTS: [string, string][] = [
  ["#f2f4f6", "#e5e8eb"],
  ["#eef0f3", "#dde1e6"],
  ["#f4f3f1", "#e8e6e2"],
  ["#eef1f5", "#dfe4ea"],
  ["#f0f2f4", "#e2e6ea"],
];

export default function CreatorCard({ profile }: { profile: ProfileListingItem }) {
  const [from, to] = TINTS[profile.name.charCodeAt(0) % TINTS.length];
  return (
    <Link href={`/creators/${profile.slug}`} className="group flex flex-col gap-2.5">
      <span className="relative block aspect-[4/5] overflow-hidden rounded-xl">
        {profile.cover_image_url ? (
          // eslint-disable-next-line @next/next/no-img-element
          <img
            src={`/api/backend${profile.cover_image_url}`}
            alt={`${profile.name} 대표 사진`}
            className="h-full w-full object-cover transition-transform duration-200 group-hover:scale-[1.03]"
          />
        ) : (
          <span
            className="flex h-full w-full items-center justify-center text-[44px] font-bold text-foreground/25 transition-transform duration-200 group-hover:scale-[1.03]"
            style={{ background: `linear-gradient(160deg, ${from}, ${to})` }}
          >
            {profile.name.slice(0, 1)}
          </span>
        )}
        <span className="absolute left-2.5 top-2.5 inline-flex h-6 items-center rounded-md bg-foreground/55 px-2 text-[11px] font-semibold text-white backdrop-blur-sm">
          {profile.primary_category}
        </span>
      </span>
      <span className="flex flex-col">
        <span className="text-[15px] font-semibold">{profile.name}</span>
        <span className="mt-0.5 line-clamp-2 text-[13px] text-muted-foreground">
          {profile.tagline}
        </span>
        {profile.rating_avg !== null && (
          <span className="mt-1 inline-flex items-center gap-1 text-[13px] font-semibold">
            <Star className="size-3.5 fill-foreground text-foreground" />
            {profile.rating_avg.toFixed(1)}
            <span className="font-normal text-muted-foreground/70">({profile.rating_count})</span>
          </span>
        )}
        {profile.price_from !== null && (
          <span className="mt-1 text-[15px] font-bold">
            {formatKrw(profile.price_from)}
            <span className="ml-1 text-xs font-normal text-muted-foreground/70">부터</span>
          </span>
        )}
      </span>
    </Link>
  );
}
