import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "이용약관",
  description: "crecity 서비스 이용약관 — 통신판매중개 서비스의 역할과 책임, 에스크로 결제·환불 정책을 안내합니다.",
  alternates: { canonical: "/terms" },
};

const SECTIONS: { title: string; body: string[] }[] = [
  {
    title: "제1조 (목적)",
    body: [
      "이 약관은 crecity(이하 \"회사\")가 운영하는 크리에이터 마켓플레이스 서비스(이하 \"서비스\")의 이용과 관련하여 회사와 회원 간의 권리·의무 및 책임 사항을 규정함을 목적으로 합니다.",
    ],
  },
  {
    title: "제2조 (통신판매중개자 고지)",
    body: [
      "회사는 통신판매중개자로서 브랜드 회원과 크리에이터 회원 간 거래를 위한 플랫폼을 제공할 뿐, 거래의 당사자가 아닙니다. 콘텐츠 제작물·거래 조건에 관한 책임은 해당 거래를 체결한 브랜드와 크리에이터에게 있습니다.",
      "다만 회사는 에스크로(안전거래) 방식으로 결제 대금을 보관하며, 분쟁 발생 시 중재 절차를 지원합니다.",
    ],
  },
  {
    title: "제3조 (에스크로 결제와 정산)",
    body: [
      "브랜드가 결제한 금액(플랫폼 수수료 포함)은 콘텐츠 승인 전까지 회사가 안전하게 보관합니다.",
      "브랜드가 납품물을 승인하거나 검토 기한(72시간)이 지나면 구매가 확정되고, 크리에이터에게 수수료를 제외한 금액이 적립됩니다.",
      "크리에이터가 주문을 거절하거나 수락 기한(72시간)이 지나면 결제 전액이 브랜드에게 크레딧으로 환불됩니다.",
    ],
  },
  {
    title: "제4조 (취소·환불)",
    body: [
      "진행 중인 주문은 양측이 합의한 경우 취소할 수 있으며, 취소가 확정되면 결제 전액이 브랜드에게 크레딧으로 환불됩니다.",
      "환불 크레딧은 다음 주문 결제 시 사용할 수 있습니다.",
    ],
  },
  {
    title: "제5조 (회원의 의무)",
    body: [
      "회원은 타인의 권리를 침해하거나 관련 법령(표시·광고의 공정화에 관한 법률 등)을 위반하는 콘텐츠를 제작·의뢰해서는 안 됩니다.",
      "광고·협찬 콘텐츠에는 관련 법령에 따른 경제적 이해관계 표시가 포함되어야 합니다.",
    ],
  },
  {
    title: "부칙",
    body: ["이 약관은 2026년 8월 11일부터 적용됩니다."],
  },
];

export default function TermsPage() {
  return (
    <div className="mx-auto max-w-3xl px-4 py-14 sm:px-6">
      <h1 className="text-[26px] font-bold tracking-[-0.02em]">이용약관</h1>
      <div className="mt-8 grid gap-8">
        {SECTIONS.map((section) => (
          <section key={section.title}>
            <h2 className="text-[15px] font-semibold">{section.title}</h2>
            {section.body.map((paragraph) => (
              <p key={paragraph} className="mt-2 text-sm leading-relaxed text-muted-foreground">
                {paragraph}
              </p>
            ))}
          </section>
        ))}
      </div>
    </div>
  );
}
