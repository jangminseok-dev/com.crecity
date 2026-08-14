import type { Metadata } from "next";
import Link from "next/link";

import { Card, CardContent } from "@/components/ui/card";
import { backendGet } from "@/lib/server/backend-api";

/**
 * 이용 방법 안내(§2.1-11 "How does it work?", 갭 #47).
 *
 * **지금 구현된 규칙만 적는다.** 수수료율처럼 설정으로 바뀌는 값은 하드코딩하지 않고
 * 백엔드 정책 API(갭 #62)에서 읽는다 — 설정이 바뀌면 이 페이지도 따라간다.
 */

type FeePolicy = {
  brand_fee_percent: number;
  creator_fee_percent: number;
  withdrawal_tax_permille: number;
  response_deadline_hours: number;
};

const CTA_CLASS =
  "inline-flex h-10 items-center justify-center rounded-md bg-primary px-5 text-sm font-semibold text-primary-foreground transition-colors hover:bg-accent-foreground";

const TITLE = "이용 방법 — 탐색부터 정산까지";
const DESCRIPTION =
  "크리에이터 탐색·에스크로 결제·납품·승인·정산이 어떻게 이어지는지 단계별로 설명합니다. 대금은 콘텐츠를 승인하기 전까지 크리시티가 보관합니다.";

export const metadata: Metadata = {
  title: TITLE,
  description: DESCRIPTION,
  alternates: { canonical: "/how-it-works" },
  openGraph: { title: TITLE, description: DESCRIPTION, type: "website" },
};

const BRAND_STEPS: { title: string; body: string }[] = [
  {
    title: "크리에이터를 찾습니다",
    body: "카테고리·키워드·플랫폼·가격대·지역으로 걸러 비교합니다. 가격이 공개된 패키지라 견적 문의 없이 바로 예산을 세울 수 있고, 마음에 드는 크리에이터는 찜해 두고 나란히 비교할 수 있습니다. 검색과 열람에 구독료는 없습니다.",
  },
  {
    title: "필요하면 먼저 이야기합니다",
    body: "결제 전에 채팅으로 일정·요구사항을 맞출 수 있습니다. 공개된 패키지에 없는 조건이라면 크리에이터가 커스텀 오퍼로 조건과 금액을 제안합니다. 반대로 조건을 걸어 공개 모집(캠페인)을 올리고 지원자 중에서 고르는 방법도 있습니다.",
  },
  {
    title: "결제하면 대금이 보관됩니다",
    body: "결제 금액은 크리에이터에게 바로 넘어가지 않고 크리시티가 보관합니다(에스크로). 여러 크리에이터를 장바구니에 담아 한 번에 결제하면 주문이 각각 만들어집니다. 결제 수단은 토스페이먼츠이며, 환불받은 크레딧이 있으면 결제액에서 먼저 차감됩니다.",
  },
  {
    title: "크리에이터가 72시간 안에 수락합니다",
    body: "수락하면 작업이 시작됩니다. 거절하거나 72시간 동안 응답이 없으면 주문은 자동으로 종료되고 결제액 전액이 크레딧으로 돌아옵니다. 이 크레딧은 다음 결제에 바로 쓸 수 있습니다. 응답 없이 넘긴 크리에이터는 인기 순위에서 불이익을 받습니다.",
  },
  {
    title: "납품물을 받고 검토합니다",
    body: "크리에이터가 결과물(파일 또는 게시물 링크)을 올리면 검토 요청 상태가 됩니다. 수정이 필요하면 수정을 요청합니다 — 요청 가능 횟수는 주문할 때 패키지 조건으로 정해져 주문에 남습니다. 게시물 링크에 광고·협찬 표기가 보이지 않으면 화면에 경고가 뜹니다(표시광고법 대응).",
  },
  {
    title: "승인하면 정산됩니다",
    body: "승인하는 순간 대금이 크리에이터 잔액으로 넘어가고 주문이 완료됩니다. 72시간 동안 아무 조치가 없으면 자동으로 승인됩니다 — 크리에이터가 무한정 기다리지 않게 하는 장치입니다. 완료된 주문에는 소통·일정·만족도 3가지 항목으로 후기를 남길 수 있습니다.",
  },
];

const CREATOR_STEPS: { title: string; body: string }[] = [
  {
    title: "프로필을 등록하고 심사를 받습니다",
    body: "소개·활동 지역·카테고리를 등록하고 판매할 패키지의 가격을 직접 정합니다. 채널 지표(팔로워·참여율)는 스크린샷과 함께 직접 입력합니다. 등록한 프로필은 운영자 심사를 거쳐야 공개 목록에 노출됩니다.",
  },
  {
    title: "주문을 받고 72시간 안에 답합니다",
    body: "브랜드가 결제하면 수락 대기 주문이 생깁니다. 수락 전까지는 작업 의무가 없고, 조건이 맞지 않으면 거절하면 됩니다. 다만 응답 없이 72시간을 넘기면 자동 종료되고 인기 순위에 불이익이 있으니 거절이라도 남기는 편이 낫습니다.",
  },
  {
    title: "작업하고 납품물을 올립니다",
    body: "결과물을 파일이나 게시물 링크로 올려야 검토 요청이 됩니다. 납품 기록은 지워지지 않고 쌓여 분쟁이 생겼을 때 근거가 됩니다. 작업 범위가 늘어났다면 진행 중에 금액 변경을 요청할 수 있고, 브랜드가 수락하면 늘어난 금액만 추가로 결제됩니다.",
  },
  {
    title: "승인되면 잔액에 쌓입니다",
    body: "브랜드가 승인하거나 72시간이 지나 자동 승인되면 수수료를 뺀 금액이 잔액으로 적립됩니다. 대금은 이미 에스크로에 들어와 있으므로 '작업하고 못 받는' 상황이 생기지 않습니다.",
  },
  {
    title: "원할 때 인출합니다",
    body: "잔액이 쌓이면 인출을 신청합니다. 사업소득 원천징수 3.3%를 뗀 금액이 지급되며, 신청 시점의 세액과 실지급액이 기록으로 남습니다. 연말에는 연간 지급명세서를 직접 확인하고 인쇄할 수 있습니다.",
  },
];

function buildFaqs(policy: FeePolicy | null): { question: string; answer: string }[] {
  const fee = policy
    ? `브랜드는 상품 금액에 중개 수수료 ${policy.brand_fee_percent}%가 더해진 금액을 결제하고, 크리에이터는 상품 금액에서 중개 수수료 ${policy.creator_fee_percent}%를 뺀 금액을 받습니다(인출 시 사업소득 원천징수 ${(policy.withdrawal_tax_permille / 10).toFixed(1)}% 별도). 주문할 때의 요율이 그 주문에 그대로 남으므로 이후 요율이 바뀌어도 진행 중인 주문에는 영향이 없습니다.`
    : "브랜드는 결제할 때 수수료가 더해진 총액을 내고, 크리에이터는 수수료를 뺀 금액을 받습니다. 정확한 금액은 결제 화면과 주문 상세에서 확인할 수 있습니다.";
  return [
  {
    question: "수수료는 얼마인가요?",
    answer: fee,
  },
  {
    question: "결제한 돈은 언제 크리에이터에게 넘어가나요?",
    answer:
      "브랜드가 납품물을 승인하는 시점입니다. 검토 요청 후 72시간 동안 아무 조치가 없으면 자동 승인되어 함께 정산됩니다. 그 전까지는 크리시티가 보관합니다.",
  },
  {
    question: "주문을 취소할 수 있나요?",
    answer:
      "진행 중인 주문은 어느 쪽이든 취소를 요청할 수 있지만 상대방이 동의해야 취소됩니다. 취소되면 브랜드에게 전액이 크레딧으로 돌아갑니다. 상대가 거부하면 주문은 그대로 진행됩니다.",
  },
  {
    question: "합의가 안 되면 어떻게 하나요?",
    answer:
      "분쟁을 신고하면 운영자가 양측 기록(납품물·대화·수정 이력)을 확인해 판정합니다. 판정 결과는 브랜드 환불, 크리에이터 지급, 신고 기각 중 하나입니다. 분쟁이 접수된 주문은 판정이 날 때까지 자동 승인이 멈춥니다.",
  },
  {
    question: "환불받은 돈은 어떻게 되나요?",
    answer:
      "계정 크레딧으로 즉시 돌아옵니다. 출금 절차를 기다릴 필요 없이 다음 주문 결제에 바로 쓸 수 있고, 결제액이 크레딧보다 적으면 남은 금액은 그대로 남습니다.",
  },
  {
    question: "크리에이터는 세금을 어떻게 처리하나요?",
    answer:
      "인출할 때 사업소득 원천징수를 떼고 지급합니다. 인출 건별 세액과 실지급액이 기록되고, 연간 지급명세서를 직접 조회·인쇄할 수 있습니다.",
  },
  ];
}

function StepList({ steps }: { steps: { title: string; body: string }[] }) {
  return (
    <ol className="mt-5 grid gap-5">
      {steps.map((step, index) => (
        <li key={step.title} className="flex gap-4">
          <span className="mt-0.5 inline-flex size-7 shrink-0 items-center justify-center rounded-full bg-accent text-[13px] font-bold text-accent-foreground">
            {index + 1}
          </span>
          <div>
            <h3 className="text-[17px] font-semibold">{step.title}</h3>
            <p className="mt-1.5 text-[15px] leading-relaxed text-muted-foreground">{step.body}</p>
          </div>
        </li>
      ))}
    </ol>
  );
}

export default async function HowItWorksPage() {
  const policy = await backendGet<FeePolicy>("/order/fee-policy");
  const faqs = buildFaqs(policy);

  return (
    <div className="mx-auto max-w-3xl px-4 pb-16 pt-10 sm:px-6">
      <nav className="text-sm text-muted-foreground">
        <Link href="/" className="hover:text-foreground">
          크리에이터 찾기
        </Link>
        <span className="mx-1.5">/</span>
        <span className="text-foreground">이용 방법</span>
      </nav>

      <h1 className="mt-4 text-[32px] font-bold leading-tight tracking-[-0.02em]">
        크리시티는 이렇게 진행돼요
      </h1>
      <p className="mt-3 text-lg text-muted-foreground">
        크리에이터를 찾고, 조건을 맞추고, 결제하고, 결과물을 받는 과정이 한 곳에서 이어집니다.
        결제한 대금은 콘텐츠를 승인하기 전까지 크리시티가 보관합니다.
      </p>
      <Link href="/" className={`${CTA_CLASS} mt-6`}>
        크리에이터 둘러보기
      </Link>

      {/* 에스크로 — 이 서비스의 핵심 차별점이라 흐름 설명보다 먼저 둔다 */}
      <Card className="mt-10 border-accent bg-accent/40">
        <CardContent className="p-6">
          <h2 className="text-lg font-bold tracking-[-0.02em]">돈은 어떻게 움직이나요</h2>
          <p className="mt-2 text-[15px] leading-relaxed text-secondary-foreground">
            브랜드가 결제한 대금은 크리에이터에게 바로 가지 않고 크리시티가 맡아 둡니다. 브랜드가
            결과물을 승인해야 크리에이터 잔액으로 넘어갑니다. 그래서 브랜드는 &ldquo;돈만 내고 못
            받는&rdquo; 위험이, 크리에이터는 &ldquo;일하고 못 받는&rdquo; 위험이 없습니다. 주문이
            취소·환불되면 대금은 브랜드 크레딧으로 즉시 돌아옵니다.
          </p>
        </CardContent>
      </Card>

      <section className="mt-12">
        <h2 className="text-xl font-bold tracking-[-0.02em]">브랜드 — 섭외부터 승인까지</h2>
        <StepList steps={BRAND_STEPS} />
      </section>

      <section className="mt-12">
        <h2 className="text-xl font-bold tracking-[-0.02em]">크리에이터 — 등록부터 인출까지</h2>
        <StepList steps={CREATOR_STEPS} />
      </section>

      <section className="mt-12">
        <h2 className="text-xl font-bold tracking-[-0.02em]">자주 묻는 질문</h2>
        <div className="mt-4 grid gap-3">
          {faqs.map((faq) => (
            <Card key={faq.question}>
              <CardContent className="p-5">
                <h3 className="text-[15px] font-semibold">{faq.question}</h3>
                <p className="mt-1.5 text-[15px] leading-relaxed text-muted-foreground">
                  {faq.answer}
                </p>
              </CardContent>
            </Card>
          ))}
        </div>
      </section>

      <section className="mt-12 border-t pt-8">
        <h2 className="text-[15px] font-semibold">더 알아보기</h2>
        <div className="mt-3.5 flex flex-wrap gap-2">
          {[
            { label: "마케팅팀을 위한 안내", href: "/for/marketing-teams" },
            { label: "크리에이터 등록 안내", href: "/for/creators" },
            { label: "단가·참여율 계산기", href: "/tools" },
            { label: "이용약관", href: "/terms" },
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
      </section>
    </div>
  );
}
