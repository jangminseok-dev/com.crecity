import type { Metadata } from "next";

import CampaignBriefBuilder from "@/components/campaign-brief-builder";

const TITLE = "캠페인 브리프 템플릿 — 인플루언서 섭외 요청서 만들기";
const DESCRIPTION =
  "인플루언서·UGC 캠페인 브리프를 항목만 채우면 완성합니다. 요청 콘텐츠·필수 포함·2차 활용 범위·광고 표기까지 빠짐없이 담은 요청서를 회원가입 없이 만들어 보세요.";

export const metadata: Metadata = {
  title: TITLE,
  description: DESCRIPTION,
  alternates: { canonical: "/tools/campaign-brief" },
  openGraph: { title: TITLE, description: DESCRIPTION, type: "website" },
};

export default function CampaignBriefPage() {
  return (
    <div className="mx-auto max-w-3xl px-4 py-14 sm:px-6">
      <h1 className="text-[28px] font-extrabold tracking-[-0.02em]">캠페인 브리프 템플릿</h1>
      <p className="mt-2 text-[15px] text-muted-foreground">
        무엇을 적어야 할지 고민하지 말고 항목만 채우세요. 크리에이터가 바로 이해할 수 있는
        요청서가 만들어집니다. 빈 항목은 무엇을 더 적어야 하는지 표시됩니다.
      </p>
      <CampaignBriefBuilder />
    </div>
  );
}
