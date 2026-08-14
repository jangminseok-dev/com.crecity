import Link from "next/link";

import { PROFILE_SORTS, type ProfileSort } from "@/lib/labels";

/** 목록 정렬 탭(§3.1, 갭 #45) — 상태 없이 URL로 수렴한다(링크 = GET). */
export default function SortTabs({
  current,
  hrefFor,
}: {
  current: ProfileSort;
  hrefFor: (sort: ProfileSort) => string;
}) {
  return (
    <div className="flex shrink-0 items-center gap-1.5">
      {PROFILE_SORTS.map((sort) => (
        <Link
          key={sort.value}
          href={hrefFor(sort.value)}
          aria-current={sort.value === current ? "true" : undefined}
          className={`inline-flex h-8 items-center rounded-full px-3.5 text-[13px] transition-colors ${
            sort.value === current
              ? "bg-secondary font-semibold text-foreground"
              : "text-muted-foreground hover:text-foreground"
          }`}
        >
          {sort.label}
        </Link>
      ))}
    </div>
  );
}
