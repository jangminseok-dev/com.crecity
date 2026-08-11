"use client";

import { Star, Trash2 } from "lucide-react";
import Link from "next/link";
import { useEffect, useState } from "react";

import { Button } from "@/components/ui/button";
import { formatKrw } from "@/lib/labels";
import { useShortlistStore } from "@/lib/shortlist-store";

/** 찜한 크리에이터 비교(§3.1) — 카테고리·지역·최저가·평점을 한 표에서 나란히 본다. */
export default function ShortlistPage() {
  const { items, remove, clear } = useShortlistStore();
  // localStorage 복원 전 렌더를 막아 SSR 결과와 어긋나지 않게 한다
  const [mounted, setMounted] = useState(false);
  useEffect(() => setMounted(true), []);

  if (!mounted) return null;

  if (items.length === 0) {
    return (
      <div className="mx-auto max-w-3xl px-4 py-20 text-center">
        <p className="text-muted-foreground">
          찜한 크리에이터가 없습니다 — 카드의 하트를 눌러 저장해 보세요.
        </p>
        <Button className="mt-4" nativeButton={false} render={<Link href="/">크리에이터 찾기</Link>} />
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-5xl px-4 py-12 sm:px-6">
      <div className="flex items-end justify-between gap-4">
        <div>
          <h1 className="text-[26px] font-bold tracking-[-0.02em]">찜한 크리에이터</h1>
          <p className="mt-1 text-sm text-muted-foreground">
            {items.length}명을 비교하고 있어요 — 이 목록은 이 브라우저에만 저장됩니다.
          </p>
        </div>
        <button
          type="button"
          onClick={clear}
          className="shrink-0 text-sm text-muted-foreground transition-colors hover:text-destructive"
        >
          전체 비우기
        </button>
      </div>

      <div className="mt-7 overflow-x-auto">
        <table className="w-full min-w-[640px] border-separate border-spacing-0 text-sm">
          <thead>
            <tr className="text-left text-muted-foreground">
              <th className="border-b pb-2.5 font-medium">크리에이터</th>
              <th className="border-b pb-2.5 font-medium">카테고리</th>
              <th className="border-b pb-2.5 font-medium">지역</th>
              <th className="border-b pb-2.5 font-medium">최저가</th>
              <th className="border-b pb-2.5 font-medium">평점</th>
              <th className="border-b pb-2.5" />
            </tr>
          </thead>
          <tbody>
            {items.map((item) => (
              <tr key={item.slug}>
                <td className="border-b py-3.5">
                  <Link href={`/creators/${item.slug}`} className="flex items-center gap-3">
                    {item.cover_image_url ? (
                      // eslint-disable-next-line @next/next/no-img-element
                      <img
                        src={`/api/backend${item.cover_image_url}`}
                        alt={item.name}
                        className="size-11 shrink-0 rounded-lg object-cover"
                      />
                    ) : (
                      <span className="flex size-11 shrink-0 items-center justify-center rounded-lg bg-secondary text-sm font-bold text-foreground/40">
                        {item.name.slice(0, 1)}
                      </span>
                    )}
                    <span className="min-w-0">
                      <span className="block font-semibold underline-offset-2 hover:underline">
                        {item.name}
                      </span>
                      <span className="block truncate text-[13px] text-muted-foreground">
                        {item.tagline}
                      </span>
                    </span>
                  </Link>
                </td>
                <td className="border-b py-3.5">{item.primary_category}</td>
                <td className="border-b py-3.5 text-muted-foreground">{item.location ?? "—"}</td>
                <td className="border-b py-3.5 font-semibold">
                  {item.price_from !== null ? formatKrw(item.price_from) : "—"}
                </td>
                <td className="border-b py-3.5">
                  {item.rating_avg !== null ? (
                    <span className="inline-flex items-center gap-1 font-semibold">
                      <Star className="size-3.5 fill-foreground text-foreground" />
                      {item.rating_avg.toFixed(1)}
                      <span className="font-normal text-muted-foreground/70">
                        ({item.rating_count})
                      </span>
                    </span>
                  ) : (
                    <span className="text-muted-foreground">—</span>
                  )}
                </td>
                <td className="border-b py-3.5 text-right">
                  <button
                    type="button"
                    aria-label="찜 해제"
                    onClick={() => remove(item.slug)}
                    className="inline-flex size-8 items-center justify-center rounded-full text-muted-foreground transition-colors hover:bg-secondary hover:text-destructive"
                  >
                    <Trash2 className="size-4" />
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
