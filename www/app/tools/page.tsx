import { Calculator, TrendingUp } from "lucide-react";
import type { Metadata } from "next";
import Link from "next/link";

export const metadata: Metadata = {
  title: "무료 도구 — 인플루언서 단가·참여율 계산기",
  description:
    "인플루언서 마케팅에 필요한 무료 도구 모음 — 광고 단가 계산기와 참여율 계산기를 회원가입 없이 바로 사용해 보세요.",
  alternates: { canonical: "/tools" },
};

const TOOLS = [
  {
    href: "/tools/pricing-calculator",
    icon: Calculator,
    title: "인플루언서 광고 단가 계산기",
    desc: "플랫폼·팔로워·참여율로 콘텐츠 1건의 적정 단가 범위를 계산해요",
  },
  {
    href: "/tools/engagement-calculator",
    icon: TrendingUp,
    title: "참여율 계산기",
    desc: "팔로워·좋아요·댓글로 계정의 참여율을 확인하고 벤치마크와 비교해요",
  },
];

export default function ToolsPage() {
  return (
    <div className="mx-auto max-w-3xl px-4 py-14 sm:px-6">
      <h1 className="text-[28px] font-extrabold tracking-[-0.02em]">무료 도구</h1>
      <p className="mt-2 text-[15px] text-muted-foreground">
        인플루언서 마케팅을 준비할 때 필요한 계산기를 회원가입 없이 사용해 보세요.
      </p>
      <div className="mt-8 grid gap-4 sm:grid-cols-2">
        {TOOLS.map((tool) => (
          <Link
            key={tool.href}
            href={tool.href}
            className="rounded-2xl border p-6 transition-colors hover:border-primary"
          >
            <tool.icon className="size-7 text-primary" />
            <p className="mt-3.5 font-semibold">{tool.title}</p>
            <p className="mt-1.5 text-[13px] leading-relaxed text-muted-foreground">{tool.desc}</p>
          </Link>
        ))}
      </div>
    </div>
  );
}
