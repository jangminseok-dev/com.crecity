import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";

import { BLOG_POSTS, findBlogPost } from "@/lib/blog";

type PageParams = Promise<{ slug: string }>;

export function generateStaticParams() {
  return BLOG_POSTS.map((post) => ({ slug: post.slug }));
}

/** 블로그 본문(§7-4, 갭 #69) — 쿼리 없는 정적 경로라 그대로 인덱싱된다. */
export async function generateMetadata({ params }: { params: PageParams }): Promise<Metadata> {
  const post = findBlogPost((await params).slug);
  if (!post) return {};
  return {
    title: post.title,
    description: post.metaDescription,
    alternates: { canonical: `/blog/${post.slug}` },
    openGraph: {
      title: post.title,
      description: post.metaDescription,
      type: "article",
      publishedTime: post.publishedAt,
    },
  };
}

export default async function BlogPostPage({ params }: { params: PageParams }) {
  const post = findBlogPost((await params).slug);
  if (!post) notFound();

  const others = BLOG_POSTS.filter((item) => item.slug !== post.slug);

  return (
    <div className="mx-auto max-w-3xl px-4 pb-16 pt-10 sm:px-6">
      <nav className="text-sm text-muted-foreground">
        <Link href="/blog" className="hover:text-foreground">
          블로그
        </Link>
        <span className="mx-1.5">/</span>
        <span className="text-foreground">{post.title}</span>
      </nav>

      <h1 className="mt-4 text-[32px] font-bold leading-tight tracking-[-0.02em]">{post.title}</h1>
      <p className="mt-2 text-sm text-muted-foreground">{post.publishedAt}</p>
      <p className="mt-4 text-lg leading-relaxed text-muted-foreground">{post.lead}</p>

      <div className="mt-12 grid gap-10">
        {post.sections.map((section) => (
          <section key={section.heading}>
            <h2 className="text-xl font-bold tracking-[-0.02em]">{section.heading}</h2>
            {section.paragraphs.map((paragraph) => (
              <p key={paragraph} className="mt-3 text-[15px] leading-relaxed text-muted-foreground">
                {paragraph}
              </p>
            ))}
            {section.list ? (
              <ul className="mt-3 grid list-disc gap-2 pl-5 text-[15px] leading-relaxed text-muted-foreground">
                {section.list.map((item) => (
                  <li key={item}>{item}</li>
                ))}
              </ul>
            ) : null}
          </section>
        ))}
      </div>

      <section className="mt-12 rounded-xl border p-6">
        <p className="font-semibold">함께 보면 좋은 것</p>
        <ul className="mt-3 grid gap-1.5 text-sm">
          {post.related.map((item) => (
            <li key={item.href}>
              <Link
                href={item.href}
                className="text-muted-foreground underline underline-offset-2 hover:text-foreground"
              >
                {item.label}
              </Link>
            </li>
          ))}
        </ul>
      </section>

      <nav className="mt-10 border-t pt-6">
        <p className="text-sm font-semibold">다른 글</p>
        <ul className="mt-2 grid gap-1.5 text-sm">
          {others.map((item) => (
            <li key={item.slug}>
              <Link
                href={`/blog/${item.slug}`}
                className="text-muted-foreground underline underline-offset-2 hover:text-foreground"
              >
                {item.title}
              </Link>
            </li>
          ))}
        </ul>
      </nav>
    </div>
  );
}
