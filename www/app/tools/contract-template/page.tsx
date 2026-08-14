import type { Metadata } from "next";
import Link from "next/link";

import { Card, CardContent } from "@/components/ui/card";

/**
 * 인플루언서 협업 계약서 템플릿(§3.9 무료 도구 · §9.2 표준계약 조항, 갭 #50).
 *
 * 크리시티에서 주문하면 조건이 자동으로 남으므로(갭 #52 조건 확인서) 이 페이지는
 * **플랫폼 밖에서 직접 계약할 때 쓰는 참고 양식**이다. 법률 자문이 아님을 분명히 한다.
 */

const TITLE = "인플루언서 협업 계약서 템플릿 — 무료 양식";
const DESCRIPTION =
  "인플루언서·UGC 협업 계약서에 꼭 들어가야 할 조항을 정리한 무료 템플릿입니다. 결과물 범위·2차 활용·수정 횟수·대금 지급·광고 표기까지 빠뜨리기 쉬운 항목을 담았습니다.";

export const metadata: Metadata = {
  title: TITLE,
  description: DESCRIPTION,
  alternates: { canonical: "/tools/contract-template" },
  openGraph: { title: TITLE, description: DESCRIPTION, type: "website" },
};

/* 조항별 들어갈 내용과 '왜 필요한지' — 빠뜨리면 분쟁이 되는 순서로 배치했다 */
const CLAUSES: { title: string; body: string; why: string }[] = [
  {
    title: "제1조 (당사자와 목적)",
    body: "브랜드(발주자)와 크리에이터(수행자)의 상호·주소·연락처를 적고, 어떤 홍보를 위한 계약인지 한 문장으로 밝힙니다.",
    why: "분쟁 시 누가 누구와 무엇을 약속했는지가 가장 먼저 확인됩니다.",
  },
  {
    title: "제2조 (결과물의 범위)",
    body: "플랫폼·형식·분량·개수를 숫자로 적습니다. 예: 인스타그램 릴스 1편(30~45초), 피드 사진 2장, 스토리 1회 공유.",
    why: "\"영상 하나\"처럼 적으면 길이·편집 수준에 대한 기대가 서로 다릅니다.",
  },
  {
    title: "제3조 (일정)",
    body: "초안 제출일, 브랜드 피드백 기한, 최종 게시일, 게시물 유지 기간을 각각 적습니다.",
    why: "피드백이 늦어져 게시가 밀리는 상황의 책임 소재를 미리 정해 둡니다.",
  },
  {
    title: "제4조 (대금과 지급 시기)",
    body: "금액(부가세 포함 여부 명시), 지급 조건과 시점, 지급 수단을 적습니다. 개인 크리에이터라면 사업소득 원천징수 3.3% 공제 여부를 함께 밝힙니다.",
    why: "세금 처리를 적지 않으면 실수령액이 예상과 달라 다툼이 생깁니다.",
  },
  {
    title: "제5조 (수정 요청)",
    body: "요청 가능 횟수와 범위를 정합니다. 예: 원 기획 범위 내 2회까지, 콘셉트 전면 변경은 별도 협의.",
    why: "무제한 수정은 크리에이터에게, 수정 불가는 브랜드에게 불리합니다.",
  },
  {
    title: "제6조 (2차 활용 범위)",
    body: "브랜드가 결과물을 어디에 얼마나 쓸 수 있는지 적습니다. 예: 자사 SNS 재게시 3개월 허용, 유료 광고 소재 사용은 별도 협의, 오프라인 인쇄물 제외.",
    why: "가장 자주 빠지는 조항입니다. 적지 않으면 유료 광고 전환 시 추가 보상 다툼이 생깁니다.",
  },
  {
    title: "제7조 (초상권·저작권)",
    body: "저작권 귀속과 크리에이터 초상 사용 범위를 정합니다. 통상 저작권은 크리에이터에게 두고 브랜드에 이용 허락을 주는 형태가 많습니다.",
    why: "\"저작권 전부 양도\"는 크리에이터가 자기 콘텐츠를 포트폴리오에도 못 쓰게 만들 수 있습니다.",
  },
  {
    title: "제8조 (광고 표기)",
    body: "대가를 받은 콘텐츠임을 게시물에 명확히 표시한다고 적습니다(예: 광고, 협찬).",
    why: "「표시·광고의 공정화에 관한 법률」상 의무이며, 위반 시 브랜드도 책임을 집니다.",
  },
  {
    title: "제9조 (비밀 유지)",
    body: "출시 전 제품 정보 등 공개하면 안 되는 내용과 그 기간을 정합니다.",
    why: "신제품 사전 협업에서 특히 중요합니다.",
  },
  {
    title: "제10조 (해지와 분쟁)",
    body: "어떤 경우에 계약을 끝낼 수 있는지, 그때 대금은 어떻게 정산하는지, 다툼이 생기면 어디서 해결할지를 정합니다.",
    why: "중간에 그만두는 상황을 미리 정해 두지 않으면 정산 기준이 없습니다.",
  },
];

export default function ContractTemplatePage() {
  return (
    <div className="mx-auto max-w-3xl px-4 py-14 sm:px-6">
      <h1 className="text-[28px] font-extrabold tracking-[-0.02em]">
        인플루언서 협업 계약서 템플릿
      </h1>
      <p className="mt-2 text-[15px] text-muted-foreground">
        직접 계약할 때 빠뜨리기 쉬운 조항을 정리했습니다. 각 조항에 무엇을 적어야 하는지와 왜
        필요한지를 함께 담았습니다.
      </p>

      <Card className="mt-6 border-accent bg-accent/40">
        <CardContent className="p-5">
          <p className="text-[15px] leading-relaxed text-secondary-foreground">
            크리시티에서 주문하면 이 조항들이 <strong>주문에 자동으로 기록</strong>됩니다 —
            수정 횟수·2차 활용 범위·대금·검수 기한이 주문 시점 값으로 남고,{" "}
            <Link href="/how-it-works" className="font-semibold underline underline-offset-2">
              에스크로
            </Link>
            가 대금을 보관합니다. 이 템플릿은 <strong>플랫폼 밖에서 직접 계약할 때</strong>{" "}
            쓰세요.
          </p>
        </CardContent>
      </Card>

      <div className="mt-10 grid gap-5">
        {CLAUSES.map((clause) => (
          <section key={clause.title} className="border-t pt-5">
            <h2 className="text-[17px] font-bold">{clause.title}</h2>
            <p className="mt-2 text-[15px] leading-relaxed">{clause.body}</p>
            <p className="mt-1.5 text-[13px] leading-relaxed text-muted-foreground">
              왜 필요한가 — {clause.why}
            </p>
          </section>
        ))}
      </div>

      <p className="mt-10 rounded-xl border border-dashed p-5 text-[13px] leading-relaxed text-muted-foreground">
        이 템플릿은 일반적인 참고 자료이며 법률 자문이 아닙니다. 금액이 크거나 사용 범위가 넓은
        계약은 변호사 검토를 받으시기 바랍니다.
      </p>

      <div className="mt-8 flex flex-wrap gap-2">
        {[
          { label: "캠페인 브리프 템플릿", href: "/tools/campaign-brief" },
          { label: "단가 계산기", href: "/tools/pricing-calculator" },
          { label: "이용 방법", href: "/how-it-works" },
        ].map((link) => (
          <Link
            key={link.href}
            href={link.href}
            className="inline-flex h-9 items-center rounded-full border bg-background px-4 text-sm text-muted-foreground transition-colors hover:text-foreground"
          >
            {link.label}
          </Link>
        ))}
      </div>
    </div>
  );
}
