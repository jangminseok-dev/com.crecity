import type { Metadata } from "next";
import Link from "next/link";

import PricingCalculator from "@/components/pricing-calculator";

export const metadata: Metadata = {
  title: "인플루언서 광고 단가 계산기 — 무료",
  description:
    "인스타그램·유튜브·틱톡·블로그 인플루언서 광고 단가를 무료로 계산해 보세요. 플랫폼·팔로워 수·참여율 기반의 시장 참고치를 알려드립니다.",
  alternates: { canonical: "/tools/pricing-calculator" },
};

export default function PricingCalculatorPage() {
  return (
    <div className="mx-auto max-w-[560px] px-4 py-14 sm:px-6">
      <nav className="text-sm text-muted-foreground">
        <Link href="/tools" className="hover:text-foreground">
          무료 도구
        </Link>
        <span className="mx-1.5">/</span>
        <span className="font-medium text-foreground">단가 계산기</span>
      </nav>
      <h1 className="mt-4 text-[26px] font-bold tracking-[-0.02em]">
        인플루언서 광고 단가 계산기
      </h1>
      <p className="mt-2 text-[15px] text-muted-foreground">
        플랫폼과 팔로워 수를 넣으면 콘텐츠 1건의 적정 단가 범위를 알려드려요. 실제 가격이
        공개된 크리에이터는 crecity에서 바로 비교할 수 있습니다.
      </p>
      <div className="mt-7">
        <PricingCalculator />
      </div>
    </div>
  );
}
