import type { Metadata } from "next";
import Link from "next/link";

import EngagementCalculator from "@/components/engagement-calculator";

export const metadata: Metadata = {
  title: "인스타그램 참여율 계산기 — 무료",
  description:
    "팔로워·평균 좋아요·평균 댓글만 넣으면 인플루언서 참여율(Engagement Rate)을 계산하고 벤치마크와 비교해 드립니다.",
  alternates: { canonical: "/tools/engagement-calculator" },
};

export default function EngagementCalculatorPage() {
  return (
    <div className="mx-auto max-w-[560px] px-4 py-14 sm:px-6">
      <nav className="text-sm text-muted-foreground">
        <Link href="/tools" className="hover:text-foreground">
          무료 도구
        </Link>
        <span className="mx-1.5">/</span>
        <span className="font-medium text-foreground">참여율 계산기</span>
      </nav>
      <h1 className="mt-4 text-[26px] font-bold tracking-[-0.02em]">참여율 계산기</h1>
      <p className="mt-2 text-[15px] text-muted-foreground">
        참여율 = (평균 좋아요 + 평균 댓글) ÷ 팔로워 × 100. 협업할 크리에이터의 실질 영향력을
        확인하는 가장 기본적인 지표예요.
      </p>
      <div className="mt-7">
        <EngagementCalculator />
      </div>
    </div>
  );
}
