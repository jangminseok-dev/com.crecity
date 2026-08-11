import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "개인정보 처리방침",
  description: "crecity가 수집하는 개인정보 항목·이용 목적·보관 기간과 이용자의 권리를 안내합니다.",
  alternates: { canonical: "/privacy" },
};

const SECTIONS: { title: string; body: string[] }[] = [
  {
    title: "1. 수집하는 개인정보 항목",
    body: [
      "회원가입(소셜 로그인): 이메일 주소, 소셜 계정 식별자.",
      "크리에이터 프로필: 이름(활동명), 소개, 활동 지역, 포트폴리오 사진.",
      "정산: 은행명, 계좌번호, 예금주(크리에이터 인출 요청 시).",
      "거래 기록: 주문·결제·채팅·납품물 등 서비스 이용 과정에서 생성되는 정보.",
    ],
  },
  {
    title: "2. 이용 목적",
    body: [
      "회원 식별·인증, 마켓플레이스 거래(주문·에스크로 결제·정산) 처리, 분쟁 대응, 법령상 의무 이행(전자상거래 기록 보존, 원천징수 등).",
    ],
  },
  {
    title: "3. 보관 기간",
    body: [
      "회원 탈퇴 시 지체 없이 파기합니다. 다만 전자상거래 등에서의 소비자 보호에 관한 법률 등 관련 법령에 따라 계약·결제·분쟁 기록은 법정 기간(3~5년) 동안 보존됩니다.",
    ],
  },
  {
    title: "4. 제3자 제공·처리 위탁",
    body: [
      "결제 처리: 토스페이먼츠(주) — 결제 승인·취소 처리에 필요한 범위.",
      "그 외 이용자의 사전 동의 없이 개인정보를 제3자에게 제공하지 않습니다.",
    ],
  },
  {
    title: "5. 이용자의 권리",
    body: [
      "이용자는 언제든지 자신의 개인정보를 조회·수정하거나 삭제(회원 탈퇴)를 요청할 수 있습니다. 문의는 고객센터를 통해 접수됩니다.",
    ],
  },
  {
    title: "부칙",
    body: ["이 방침은 2026년 8월 11일부터 적용됩니다."],
  },
];

export default function PrivacyPage() {
  return (
    <div className="mx-auto max-w-3xl px-4 py-14 sm:px-6">
      <h1 className="text-[26px] font-bold tracking-[-0.02em]">개인정보 처리방침</h1>
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
