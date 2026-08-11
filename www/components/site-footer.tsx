import { ShieldCheck } from "lucide-react";

const SUPPORT = [
  "평일 09:00–18:00 (주말·공휴일 휴무)",
  "1:1 문의 — 24시간 접수",
  "브랜드·크리에이터 분쟁 중재 센터",
];
const COMPANY = ["회사소개", "채용정보", "공지사항", "블로그"];
const GUIDE = ["이용약관", "개인정보 처리방침", "환불 규정", "크리에이터 등록 안내", "입점·제휴 문의"];

export default function SiteFooter() {
  return (
    <footer className="mt-20 border-t bg-[#f9fafb]">
      <div className="mx-auto grid max-w-6xl gap-10 px-6 py-12 md:grid-cols-[1.2fr_1fr_1fr_1.4fr]">
        <div>
          <h4 className="mb-3.5 text-[15px] font-bold">고객센터 1600-0000</h4>
          <ul className="flex flex-col gap-2.5 text-[13px] text-muted-foreground">
            {SUPPORT.map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ul>
        </div>
        <div>
          <h4 className="mb-3.5 text-[15px] font-bold">크리시티</h4>
          <ul className="flex flex-col gap-2.5 text-[13px] text-muted-foreground">
            {COMPANY.map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ul>
        </div>
        <div>
          <h4 className="mb-3.5 text-[15px] font-bold">이용안내</h4>
          <ul className="flex flex-col gap-2.5 text-[13px] text-muted-foreground">
            {GUIDE.map((item) => (
              <li key={item} className={item === "개인정보 처리방침" ? "font-semibold text-foreground/70" : undefined}>
                {item}
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
      <div className="mx-auto max-w-6xl px-6">
        <div className="border-t py-6 pb-12 text-xs leading-relaxed text-muted-foreground/80">
          © 2026 crecity — 브랜드와 크리에이터를 잇는 마켓플레이스
        </div>
      </div>
    </footer>
  );
}
