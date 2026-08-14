import { ShieldCheck } from "lucide-react";
import Link from "next/link";

/* 실제로 동작하는 경로만 싣는다(갭 #61) — 없는 연락처·부서를 적어두면 그 자체가 허위 안내다.
   전화 상담·채용·공지 같은 창구는 실제로 생길 때 추가한다. */
const SUPPORT: { label: string; href: string }[] = [
  { label: "자주 묻는 질문", href: "/faq" },
  { label: "이용 방법", href: "/how-it-works" },
  { label: "주문 분쟁 중재 — 주문 상세에서 신고", href: "/how-it-works" },
];
const GUIDE: { label: string; href: string }[] = [
  { label: "이용약관", href: "/terms" },
  { label: "개인정보 처리방침", href: "/privacy" },
  { label: "환불 규정", href: "/terms" },
  { label: "무료 도구 — 계산기·템플릿", href: "/tools" },
  { label: "마케팅팀을 위한 안내", href: "/for/marketing-teams" },
  { label: "창업가를 위한 안내", href: "/for/founders" },
  { label: "크리에이터 등록 안내", href: "/for/creators" },
];

export default function SiteFooter() {
  return (
    <footer className="mt-20 border-t bg-[#f9fafb]">
      <div className="mx-auto grid max-w-6xl gap-10 px-4 py-12 sm:px-6 md:grid-cols-[1fr_1fr_1.4fr]">
        <div>
          <h4 className="mb-3.5 text-[15px] font-bold">도움말</h4>
          <ul className="flex flex-col gap-2.5 text-[13px] text-muted-foreground">
            {SUPPORT.map((item) => (
              <li key={item.label}>
                <Link href={item.href} className="transition-colors hover:text-foreground">
                  {item.label}
                </Link>
              </li>
            ))}
          </ul>
        </div>
        <div>
          <h4 className="mb-3.5 text-[15px] font-bold">이용안내</h4>
          <ul className="flex flex-col gap-2.5 text-[13px] text-muted-foreground">
            {GUIDE.map((item) => (
              <li
                key={item.label}
                className={item.label === "개인정보 처리방침" ? "font-semibold text-foreground/70" : undefined}
              >
                <Link href={item.href} className="transition-colors hover:text-foreground">
                  {item.label}
                </Link>
              </li>
            ))}
          </ul>
        </div>
        <div>
          <h4 className="mb-3.5 text-[15px] font-bold">안전거래</h4>
          <div className="flex items-start gap-2.5 rounded-xl border bg-background px-4 py-3.5 text-[13px] leading-relaxed text-muted-foreground">
            <ShieldCheck className="mt-0.5 size-5 shrink-0 text-primary" />
            모든 결제 금액은 콘텐츠 승인 전까지 크리시티가 에스크로로 안전하게 보관해요.
          </div>
        </div>
      </div>
      <div className="mx-auto max-w-6xl px-4 sm:px-6">
        <div className="border-t py-6 pb-12 text-xs leading-relaxed text-muted-foreground/80">
          <p>
            crecity는 통신판매중개자로서 거래 당사자가 아니며, 상품 정보·거래에 관한 책임은
            각 판매 크리에이터에게 있습니다. 다만 결제 대금은 콘텐츠 승인 전까지 에스크로로
            보관됩니다.
          </p>
          <p className="mt-2">© 2026 crecity — 브랜드와 크리에이터를 잇는 마켓플레이스</p>
        </div>
      </div>
    </footer>
  );
}
