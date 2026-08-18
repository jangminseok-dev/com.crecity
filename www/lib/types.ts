// 백엔드 응답 타입 — 필드명은 백엔드(snake_case) 그대로, 변환하지 않는다(루트 CLAUDE.md 규칙).

export type ProfileListingItem = {
  id: number;
  slug: string;
  name: string;
  tagline: string;
  location: string | null;
  primary_category: string;
  created_at: string | null;
  cover_image_url: string | null; // 정적 서빙 경로 — /api/backend 프리픽스 붙여 사용
  price_from: number | null; // 최저 패키지 가격
  rating_avg: number | null;
  rating_count: number;
};

export type ProfileListingResponse = {
  items: ProfileListingItem[];
  total: number;
};

export type CreatorProfile = {
  id: number;
  slug: string;
  name: string;
  tagline: string;
  bio: string;
  location: string | null;
  primary_category: string;
  status: "PENDING" | "APPROVED" | "REJECTED";
  created_at: string | null;
  followers_total: number; // 전 채널 팔로워 합(자가입력) — 헤더 배지
  accepting_orders: boolean; // 주문 수신 여부(갭 #64)
  // 거래 실적(갭 #66) — 받은 주문이 없으면 null
  completed_orders: number | null;
  accepted_orders: number | null;
  received_orders: number | null;
  // 응답 지표(갭 #80) — 전이 이력 표본이 없으면 null
  avg_accept_hours: number | null;
  fast_responder: boolean;
};

export type ProfileFaq = {
  id: number;
  question: string;
  answer: string;
  created_at: string | null;
};

export type ProfileAnalytics = {
  platform: "INSTAGRAM" | "YOUTUBE" | "TIKTOK" | "NAVER_BLOG";
  followers_count: number;
  engagement_permille: number | null; // 참여율 ×10 (3.5% → 35)
  screenshot_url: string;
  updated_at: string | null;
  // 오디언스(§2.1-6, 갭 #67)
  top_audience_region: string | null;
  audience: { dimension: string; bucket: string; share_permille: number }[];
};

export type Order = {
  id: number;
  package_id: number;
  package_title: string;
  brand_user_id: number;
  creator_user_id: number;
  amount_krw: number;
  brand_total_krw: number;
  creator_payout_krw: number;
  brand_fee_percent: number;
  creator_fee_percent: number;
  requirements: string;
  status:
    | "PENDING_ACCEPT"
    | "IN_PROGRESS"
    | "DRAFT_REVIEW"
    | "IN_REVIEW"
    | "COMPLETED"
    | "REFUNDED"
    | "CANCELLED";
  deadline_at: string | null;
  cancel_requested_by: number | null;
  revision_limit: number;
  revisions_used: number;
  usage_rights: string;
  draft_approved: boolean; // 초안 컨펌 여부(갭 #85) — 초안 버튼 노출 판단
  created_at: string | null;
  // 거래 상대(갭 #63)와 상대의 거래 이력(갭 #65)
  counterpart_name: string | null;
  counterpart_slug: string | null;
  counterpart_completed_orders: number | null;
  counterpart_cancelled_orders: number | null;
  counterpart_accept_expired_orders: number | null;
  counterpart_total_revisions: number | null;
};

export type OrderAdjustment = {
  id: number;
  order_id: number;
  extra_amount_krw: number;
  reason: string;
  status: "REQUESTED" | "PAID" | "DECLINED";
  created_at: string | null;
};

export type Deliverable = {
  id: number;
  order_id: number;
  kind: "FILE" | "LINK";
  file_url: string | null;
  original_name: string | null;
  url: string | null;
  caption: string | null;
  ad_disclosure_ok: boolean | null; // 광고 표기 검수 — 링크만 판정(파일은 null)
  created_at: string | null;
};

export type Dispute = {
  id: number;
  order_id: number;
  raised_by_user_id: number;
  reason: string;
  status: "OPEN" | "RESOLVED";
  resolution: "REFUND" | "RELEASE" | "DISMISS" | null;
  created_at: string | null;
  resolved_at: string | null;
};

export type Campaign = {
  id: number;
  brand_user_id: number;
  title: string;
  description: string;
  platform: "INSTAGRAM" | "YOUTUBE" | "TIKTOK" | "NAVER_BLOG" | "UGC";
  budget_krw: number;
  status: "OPEN" | "CLOSED";
  deadline_at: string | null; // 지원 마감일 — 경과 시 자동 마감
  target_category: string | null;
  target_location: string | null;
  created_at: string | null;
};

export type CampaignApplication = {
  id: number;
  campaign_id: number;
  creator_user_id: number;
  creator_name: string;
  creator_slug: string;
  message: string;
  proposed_price_krw: number;
  order_id: number | null;
  created_at: string | null;
};

export type ChatConversation = {
  id: number;
  counterpart_name: string;
  counterpart_slug: string | null;
  last_message: string | null;
  last_message_at: string | null;
  unread_count: number; // 내가 안 읽은 상대 메시지 수
  created_at: string | null;
};

export type ChatMessage = {
  id: number;
  conversation_id: number;
  sender_user_id: number;
  body: string;
  is_mine: boolean;
  created_at: string | null;
  image_url: string | null; // 사진 메시지 — /api/backend 프리픽스 붙여 사용
};

export type Balance = {
  user_id: number;
  balance_krw: number;
};

export type CreatorPackage = {
  id: number;
  profile_id: number;
  platform: "INSTAGRAM" | "YOUTUBE" | "TIKTOK" | "NAVER_BLOG" | "UGC";
  title: string;
  description: string;
  price_krw: number;
  revision_limit: number; // 수정 요청 허용 횟수
  usage_rights: string; // 2차 활용 범위
  created_at: string | null;
};

export type NotificationItem = {
  id: number;
  event_type: string;
  body: string;
  link: string | null;
  is_read: boolean;
  created_at: string | null;
};

export type NotificationsResult = {
  unread_count: number;
  items: NotificationItem[];
};

export type PortfolioItem = {
  id: number;
  image_url: string;
  created_at: string | null;
};

export type CustomOffer = {
  id: number;
  conversation_id: number;
  title: string;
  price_krw: number;
  status: "PENDING" | "PAID";
  order_id: number | null;
  created_at: string | null;
};
