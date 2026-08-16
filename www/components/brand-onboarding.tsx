import Link from "next/link";

import { Card, CardContent } from "@/components/ui/card";

/**
 * 브랜드 첫 걸음 안내(갭 #78).
 *
 * 크리에이터에겐 완성도 체크리스트(갭 #58)가 있지만 브랜드는 가입 직후 할 일이 없어 보인다.
 * **구현된 경로만** 적는다 — 성과 수치·고객 사례는 쓰지 않는다(www CLAUDE.md).
 */
const STEPS = [
  {
    href: "/",
    label: "크리에이터 찾기",
    hint: "카테고리·가격대로 검색하고 프로필에서 바로 주문할 수 있어요.",
  },
  {
    href: "/dashboard/campaigns",
    label: "공고 올리기",
    hint: "원하는 조건을 적어 두면 크리에이터가 견적과 함께 지원합니다.",
  },
  {
    href: "/how-it-works",
    label: "거래 방식 확인",
    hint: "결제 대금은 구매 확정까지 보관되고, 수락·검토에는 각각 72시간이 주어집니다.",
  },
  {
    href: "/dashboard/balance",
    label: "크레딧 확인",
    hint: "취소·환불된 금액은 크레딧으로 쌓여 다음 주문에 쓸 수 있어요.",
  },
];

export default function BrandOnboarding() {
  return (
    <Card>
      <CardContent className="p-5">
        <h3 className="font-semibold">무엇부터 하면 되나요?</h3>
        <p className="mt-1 text-sm text-muted-foreground">
          아직 주문이 없습니다. 아래 순서로 시작해 보세요.
        </p>
        <ul className="mt-4 grid gap-3">
          {STEPS.map((step, index) => (
            <li key={step.href} className="flex items-start gap-2.5 text-sm">
              <span className="mt-0.5 inline-flex size-5 shrink-0 items-center justify-center rounded-full bg-secondary text-[11px] font-semibold">
                {index + 1}
              </span>
              <span>
                <Link href={step.href} className="font-semibold text-primary hover:underline">
                  {step.label}
                </Link>
                <span className="ml-1.5 text-[13px] text-muted-foreground">{step.hint}</span>
              </span>
            </li>
          ))}
        </ul>
      </CardContent>
    </Card>
  );
}
