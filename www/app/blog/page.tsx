import type { Metadata } from "next";
import Link from "next/link";

import { BLOG_POSTS } from "@/lib/blog";

export const metadata: Metadata = {
  title: "블로그 — 인플루언서 마케팅 가이드",
  description:
    "협찬 단가 책정, 캠페인 브리프 작성, 광고 표기까지 — 인플루언서 마케팅을 준비하는 브랜드와 크리에이터를 위한 가이드 모음.",
  alternates: { canonical: "/blog" },
};

/** 블로그 인덱스(§7-4, 갭 #69) — 콘텐츠 정본은 lib/blog.ts. */
export default function BlogIndexPage() {
  return (
    <div className="mx-auto max-w-3xl px-4 py-14 sm:px-6">
      <h1 className="text-[28px] font-extrabold tracking-[-0.02em]">블로그</h1>
      <p className="mt-2 text-[15px] text-muted-foreground">
        협찬 단가·브리프·광고 표기 — 인플루언서 마케팅을 준비할 때 필요한 가이드를 모았습니다.
      </p>
      <div className="mt-8 grid gap-4">
        {BLOG_POSTS.map((post) => (
          <Link
            key={post.slug}
            href={`/blog/${post.slug}`}
            className="rounded-2xl border p-6 transition-colors hover:border-primary"
          >
            <p className="text-xs text-muted-foreground">{post.publishedAt}</p>
            <p className="mt-1.5 text-lg font-semibold tracking-[-0.01em]">{post.title}</p>
            <p className="mt-2 text-[14px] leading-relaxed text-muted-foreground">
              {post.metaDescription}
            </p>
          </Link>
        ))}
      </div>
    </div>
  );
}
