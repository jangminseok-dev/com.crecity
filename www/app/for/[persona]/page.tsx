import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";

import { Card, CardContent } from "@/components/ui/card";
import { PERSONAS, findPersona } from "@/lib/personas";

// Button은 asChild를 받지 않으므로 링크형 CTA는 스타일을 직접 준다
const CTA_CLASS =
  "inline-flex h-10 items-center justify-center rounded-md bg-primary px-5 text-sm font-semibold text-primary-foreground transition-colors hover:bg-accent-foreground";

type PageParams = Promise<{ persona: string }>;

export function generateStaticParams() {
  return PERSONAS.map((persona) => ({ persona: persona.slug }));
}

/** 페르소나 랜딩(§5, 갭 #13) — 쿼리 없는 정적 경로라 그대로 인덱싱된다. */
export async function generateMetadata({ params }: { params: PageParams }): Promise<Metadata> {
  const persona = findPersona((await params).persona);
  if (!persona) return {};
  return {
    title: persona.metaTitle,
    description: persona.metaDescription,
    alternates: { canonical: `/for/${persona.slug}` },
    openGraph: { title: persona.metaTitle, description: persona.metaDescription, type: "website" },
  };
}

export default async function PersonaLandingPage({ params }: { params: PageParams }) {
  const persona = findPersona((await params).persona);
  if (!persona) notFound();

  const others = PERSONAS.filter((item) => item.slug !== persona.slug);

  return (
    <div className="mx-auto max-w-3xl px-4 pb-16 pt-10 sm:px-6">
      <nav className="text-sm text-muted-foreground">
        <Link href="/" className="hover:text-foreground">
          크리에이터 찾기
        </Link>
        <span className="mx-1.5">/</span>
        <span className="text-foreground">{persona.title}</span>
      </nav>

      <h1 className="mt-4 text-[32px] font-bold leading-tight tracking-[-0.02em]">
        {persona.title}
      </h1>
      <p className="mt-3 text-lg text-muted-foreground">{persona.lead}</p>
      <Link href={persona.ctaHref} className={`${CTA_CLASS} mt-6`}>
        {persona.ctaLabel}
      </Link>

      <div className="mt-12 grid gap-6">
        {persona.sections.map((section) => (
          <section key={section.heading}>
            <h2 className="text-xl font-bold tracking-[-0.02em]">{section.heading}</h2>
            <p className="mt-2 text-[15px] leading-relaxed text-muted-foreground">
              {section.body}
            </p>
          </section>
        ))}
      </div>

      <section className="mt-12">
        <h2 className="text-xl font-bold tracking-[-0.02em]">자주 묻는 질문</h2>
        <div className="mt-4 grid gap-3">
          {persona.faqs.map((faq) => (
            <Card key={faq.question}>
              <CardContent className="p-5">
                <p className="font-semibold">{faq.question}</p>
                <p className="mt-2 text-[15px] leading-relaxed text-muted-foreground">
                  {faq.answer}
                </p>
              </CardContent>
            </Card>
          ))}
        </div>
      </section>

      <section className="mt-12 rounded-xl border p-6">
        <p className="font-semibold">
          {persona.audience === "BRAND"
            ? "지금 등록된 크리에이터를 둘러보세요"
            : "가격을 공개하고 협찬 요청을 받아 보세요"}
        </p>
        <Link href={persona.ctaHref} className={`${CTA_CLASS} mt-4`}>
          {persona.ctaLabel}
        </Link>
      </section>

      <nav className="mt-10 border-t pt-6">
        <p className="text-sm font-semibold">다른 안내</p>
        <ul className="mt-2 grid gap-1.5 text-sm">
          {others.map((item) => (
            <li key={item.slug}>
              <Link
                href={`/for/${item.slug}`}
                className="text-muted-foreground underline underline-offset-2 hover:text-foreground"
              >
                {item.title}
              </Link>
            </li>
          ))}
          <li>
            <Link
              href="/tools"
              className="text-muted-foreground underline underline-offset-2 hover:text-foreground"
            >
              무료 도구 — 단가·참여율 계산기
            </Link>
          </li>
        </ul>
      </nav>
    </div>
  );
}
