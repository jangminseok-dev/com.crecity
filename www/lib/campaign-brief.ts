/**
 * 캠페인 브리프 템플릿(§3.9 무료 도구, 갭 #49).
 *
 * §3.2의 "AI 브리프 생성"은 LLM 연동(갭 #39)이 필요해 보류했다 — 실제로 브랜드가 겪는
 * 어려움은 "무엇을 적어야 하는지 모른다"는 쪽이므로, 항목을 정해 주는 것으로 대부분 해결된다.
 */

export type BriefFields = {
  brand: string;
  product: string;
  goal: string;
  audience: string;
  deliverable: string;
  mustInclude: string;
  avoid: string;
  schedule: string;
  usageRights: string;
};

export const BRIEF_GOALS = [
  "브랜드 인지도 확대",
  "신제품 소개",
  "구매 전환",
  "사용 후기 확보",
  "재구매 유도",
] as const;

export const EMPTY_BRIEF: BriefFields = {
  brand: "",
  product: "",
  goal: BRIEF_GOALS[0],
  audience: "",
  deliverable: "",
  mustInclude: "",
  avoid: "",
  schedule: "",
  usageRights: "",
};

/** 각 항목의 라벨·설명·예시 — 도구 화면과 골격 텍스트가 같은 문구를 쓴다. */
export const BRIEF_SECTIONS: {
  key: keyof BriefFields;
  label: string;
  placeholder: string;
  hint: string;
  multiline?: boolean;
}[] = [
  {
    key: "brand",
    label: "브랜드",
    placeholder: "예: 라이트홈",
    hint: "브랜드 이름과 한 줄 소개",
  },
  {
    key: "product",
    label: "제품·서비스",
    placeholder: "예: 저자극 수분 크림 50ml",
    hint: "홍보할 대상과 핵심 특징",
  },
  {
    key: "audience",
    label: "타겟",
    placeholder: "예: 건성 피부 고민이 있는 20~30대 여성",
    hint: "누구에게 보이고 싶은지",
  },
  {
    key: "deliverable",
    label: "요청 콘텐츠",
    placeholder: "예: 인스타그램 릴스 1편(30초 내외) + 피드 사진 2장",
    hint: "플랫폼·형식·분량을 구체적으로",
    multiline: true,
  },
  {
    key: "mustInclude",
    label: "필수 포함",
    placeholder: "예: 해시태그 #라이트홈 #수분크림, 계정 멘션 @lighthome",
    hint: "해시태그·멘션·링크·꼭 보여줄 장면",
    multiline: true,
  },
  {
    key: "avoid",
    label: "피해야 할 것",
    placeholder: "예: 경쟁 브랜드 노출, 의학적 효능 표현",
    hint: "쓰면 안 되는 표현이나 연출",
    multiline: true,
  },
  {
    key: "schedule",
    label: "일정",
    placeholder: "예: 시안 확인 3일 내, 게시 3월 2주차",
    hint: "초안 확인·게시 희망 시점",
  },
  {
    key: "usageRights",
    label: "2차 활용 범위",
    placeholder: "예: 자사 SNS 3개월 재게시 허용, 유료 광고 별도 협의",
    hint: "결과물을 브랜드가 어디까지 쓸지 — 주문 조건으로 남는다",
    multiline: true,
  },
];

/** 값이 빈 항목은 안내 문구를 남겨 무엇을 더 적어야 하는지 드러낸다. */
function line(label: string, value: string, fallback: string): string {
  return `■ ${label}\n${value.trim() || `(${fallback})`}\n`;
}

export function buildBrief(fields: BriefFields): string {
  const sections = [
    line("브랜드", fields.brand, "브랜드 이름과 한 줄 소개"),
    line("제품·서비스", fields.product, "홍보할 대상과 핵심 특징"),
    line("캠페인 목표", fields.goal, "예: 브랜드 인지도 확대"),
    line("타겟", fields.audience, "누구에게 보이고 싶은지"),
    line("요청 콘텐츠", fields.deliverable, "플랫폼·형식·분량"),
    line("필수 포함", fields.mustInclude, "해시태그·멘션·링크"),
    line("피해야 할 것", fields.avoid, "쓰면 안 되는 표현이나 연출"),
    line("일정", fields.schedule, "초안 확인·게시 희망 시점"),
    line("2차 활용 범위", fields.usageRights, "브랜드가 결과물을 어디까지 쓸지"),
  ];
  // 광고 표기는 협의 대상이 아니라 법상 의무라 항상 붙인다(표시광고법)
  return `${sections.join("\n")}\n■ 광고 표기\n대가를 받은 콘텐츠이므로 게시물에 "광고" 또는 "협찬" 표기를 반드시 포함해 주세요.\n`;
}

/** 아무것도 채우지 않은 골격 — 캠페인 등록 폼에서 바로 넣어 쓴다. */
export const BRIEF_SKELETON = buildBrief({ ...EMPTY_BRIEF, goal: "" });
