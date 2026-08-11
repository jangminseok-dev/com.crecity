"use client";

import { Heart } from "lucide-react";
import { useEffect, useState } from "react";

import { useShortlistStore, type ShortlistItem } from "@/lib/shortlist-store";

/** 찜 토글(§3.1) — 카드 위 오버레이 또는 프로필 사이드바에서 쓴다. */
export default function ShortlistButton({
  item,
  className = "",
  withLabel = false,
}: {
  item: ShortlistItem;
  className?: string;
  withLabel?: boolean;
}) {
  const { items, toggle } = useShortlistStore();
  // localStorage 복원 전에는 빈 상태로 그려야 SSR 결과와 어긋나지 않는다
  const [mounted, setMounted] = useState(false);
  useEffect(() => setMounted(true), []);

  const saved = mounted && items.some((i) => i.slug === item.slug);

  if (withLabel) {
    return (
      <button
        type="button"
        onClick={() => toggle(item)}
        className={`inline-flex h-11 w-full items-center justify-center gap-2 rounded-xl border text-sm font-semibold transition-colors hover:bg-secondary ${className}`}
      >
        <Heart className={`size-4 ${saved ? "fill-destructive text-destructive" : ""}`} />
        {saved ? "찜 목록에 저장됨" : "찜하기 — 나중에 비교"}
      </button>
    );
  }

  return (
    <button
      type="button"
      aria-label={saved ? "찜 해제" : "찜하기"}
      onClick={() => toggle(item)}
      className={`inline-flex size-8 items-center justify-center rounded-full bg-background/85 text-foreground/70 shadow-sm backdrop-blur-sm transition-colors hover:text-destructive ${className}`}
    >
      <Heart className={`size-4 ${saved ? "fill-destructive text-destructive" : ""}`} />
    </button>
  );
}
