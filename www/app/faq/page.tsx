import type { Metadata } from "next";
import Link from "next/link";

import { Card, CardContent } from "@/components/ui/card";
import { backendGet } from "@/lib/server/backend-api";

/**
 * 자주 묻는 질문·문의 안내(부록 `/faq`·`/support`, 갭 #68).
 *
 * **없는 창구를 적지 않는다**(갭 #61) — 지금 실제로 동작하는 경로만 안내한다.
 * 수수료는 하드코딩하지 않고 백엔드 정책(갭 #62)에서 읽어 설정이 바뀌면 함께 바뀐다.
 */

const TITLE = "자주 묻는 질문";
const DESCRIPTION =
  "크리시티 이용 중 자주 나오는 질문과 문의 방법을 모았습니다. 결제·정산·수수료·분쟁 처리 절차를 확인하세요.";

export const metadata: Metadata = {
  title: TITLE,
  description: DESCRIPTION,
  alternates: { canonical: "/faq" },
  openGraph: { title: TITLE, description: DESCRIPTION, type: "website" },
};

type FeePolicy = {
  brand_fee_percent: number;
  creator_fee_percent: number;
  withdrawal_tax_permille: number;
  response_deadline_hours: number;
};

type Faq = { question: string; answer: string };

function buildFaqs(policy: FeePolicy | null): { group: string; items: Faq[] }[] {
  const hours = policy?.response_deadline_hours ?? 72;
  const fee = policy
    ? `브랜드는 결제 시 상품 금액에 중개 수수료 ${policy.brand_fee_percent}%가 더해진 금액을 냅니다. 크리에이터는 상품 금액에서 중개 수수료 ${policy.creator_fee_percent}%를 뺀 금액을 받고, 인출할 때 사업소득 원천징수 ${(policy.withdrawal_tax_permille / 10).toFixed(1)}%가 추가로 공제됩니다.`
    : "수수료는 결제 화면과 주문 상세에서 확인할 수 있습니다.";

  return [
    {
      group: "결제와 정산",
      items: [
        { question: "수수료는 얼마인가요?", answer: fee },
        {
          question: "결제한 돈은 언제 크리에이터에게 넘어가나요?",
          answer: `브랜드가 결과물을 승인하는 시점입니다. 검토 요청 후 ${hours}시간 동안 아무 조치가 없으면 자동 승인되어 함께 정산됩니다. 그 전까지는 크리시티가 보관합니다(에스크로).`,
        },
        {
          question: "크리에이터는 돈을 어떻게 받나요?",
          answer:
            "승인된 대금은 잔액으로 적립되고, 원할 때 인출을 신청하면 등록한 계좌로 지급됩니다. 인출 건별 세액과 실지급액이 기록되며 연간 지급명세서를 직접 조회·인쇄할 수 있습니다.",
        },
        {
          question: "환불받은 금액은 어떻게 되나요?",
          answer:
            "계정 크레딧으로 즉시 돌아옵니다. 출금 절차를 기다릴 필요 없이 다음 결제에 바로 쓸 수 있습니다.",
        },
      ],
    },
    {
      group: "주문 진행",
      items: [
        {
          question: "크리에이터가 응답하지 않으면요?",
          answer: `주문 후 ${hours}시간 안에 수락하지 않으면 자동으로 종료되고 결제액 전액이 크레딧으로 환급됩니다. 응답 없이 넘긴 크리에이터는 인기 순위에서 불이익을 받습니다.`,
        },
        {
          question: "수정은 몇 번까지 요청할 수 있나요?",
          answer:
            "주문할 때 패키지 조건으로 정해진 횟수까지입니다. 정확한 횟수는 주문 상세와 계약 조건 확인서에서 볼 수 있습니다.",
        },
        {
          question: "주문을 취소하고 싶어요.",
          answer:
            "진행 중인 주문은 어느 쪽이든 취소를 요청할 수 있지만 상대방이 동의해야 취소됩니다. 취소되면 브랜드에게 전액이 크레딧으로 돌아갑니다.",
        },
        {
          question: "합의가 안 되면 어떻게 하나요?",
          answer:
            "주문 상세에서 분쟁을 신고하면 운영자가 납품물·대화·수정 이력을 확인해 환급·지급·기각 중 하나로 판정합니다. 분쟁이 접수된 주문은 판정이 날 때까지 자동 승인이 멈춥니다.",
        },
      ],
    },
    {
      group: "크리에이터",
      items: [
        {
          question: "입점에 비용이 드나요?",
          answer:
            "프로필 등록과 노출은 무료입니다. 거래가 성사될 때만 중개 수수료가 발생합니다.",
        },
        {
          question: "프로필 심사는 어떻게 하나요?",
          answer:
            "등록한 프로필은 운영자 확인을 거쳐 공개 목록에 노출됩니다. 채널 지표와 콘텐츠를 함께 보며, 자동 승인·반려는 하지 않습니다.",
        },
        {
          question: "당분간 주문을 받고 싶지 않아요.",
          answer:
            "대시보드 프로필 화면에서 주문 수신을 끄면 목록에서 빠지고 새 주문이 들어오지 않습니다. 진행 중인 주문에는 영향이 없습니다.",
        },
      ],
    },
    {
      group: "계정",
      items: [
        {
          question: "브랜드 계정과 크리에이터 계정을 함께 쓸 수 있나요?",
          answer:
            "같은 이메일로는 하나만 가질 수 있습니다. 계정 유형은 첫 가입 때 정해집니다.",
        },
        {
          question: "탈퇴하고 싶어요.",
          answer:
            "설정 화면에서 탈퇴할 수 있습니다. 다만 진행 중인 주문이나 남은 잔액이 있으면 정리한 뒤에 가능합니다.",
        },
      ],
    },
  ];
}

export default async function FaqPage() {
  const policy = await backendGet<FeePolicy>("/order/fee-policy");
  const groups = buildFaqs(policy);

  return (
    <div className="mx-auto max-w-3xl px-4 py-14 sm:px-6">
      <h1 className="text-[28px] font-extrabold tracking-[-0.02em]">자주 묻는 질문</h1>
      <p className="mt-2 text-[15px] text-muted-foreground">
        결제·정산·주문 진행에서 자주 나오는 질문을 모았습니다. 전체 흐름은{" "}
        <Link href="/how-it-works" className="font-medium text-primary hover:underline">
          이용 방법
        </Link>
        에서 볼 수 있습니다.
      </p>

      {groups.map((group) => (
        <section key={group.group} className="mt-10">
          <h2 className="text-xl font-bold tracking-[-0.02em]">{group.group}</h2>
          <div className="mt-4 grid gap-3">
            {group.items.map((faq) => (
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
      ))}

      <section className="mt-12 border-t pt-8">
        <h2 className="text-xl font-bold tracking-[-0.02em]">더 물어볼 곳</h2>
        <p className="mt-2 text-[15px] leading-relaxed text-muted-foreground">
          여기서 답을 찾지 못했다면 아래 경로를 이용하세요. 전화 상담 창구는 아직 없습니다.
        </p>
        <ul className="mt-4 grid gap-2 text-[15px]">
          <li>
            <strong>주문에 문제가 있을 때</strong> — 주문 상세 화면에서 분쟁을 신고하면 운영자가
            기록을 확인해 판정합니다.
          </li>
          <li>
            <strong>부적절한 프로필·대화를 봤을 때</strong> — 프로필 하단이나 채팅방 상단의 신고
            버튼을 이용하세요.
          </li>
          <li>
            <strong>거래 상대와 조건을 조율할 때</strong> — 결제 전에는 채팅으로 직접 협의할 수
            있습니다.
          </li>
        </ul>
      </section>
    </div>
  );
}
