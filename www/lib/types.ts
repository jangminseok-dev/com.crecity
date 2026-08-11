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
  status: "PENDING_ACCEPT" | "IN_PROGRESS" | "IN_REVIEW" | "COMPLETED" | "REFUNDED" | "CANCELLED";
  deadline_at: string | null;
  cancel_requested_by: number | null;
  created_at: string | null;
};

export type Deliverable = {
  id: number;
  order_id: number;
  kind: "FILE" | "LINK";
  file_url: string | null;
  original_name: string | null;
  url: string | null;
  created_at: string | null;
};

export type Campaign = {
  id: number;
  brand_user_id: number;
  title: string;
  description: string;
  platform: "INSTAGRAM" | "YOUTUBE" | "TIKTOK" | "NAVER_BLOG" | "UGC";
  budget_krw: number;
  status: "OPEN" | "CLOSED";
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
  created_at: string | null;
};

export type ChatConversation = {
  id: number;
  counterpart_name: string;
  counterpart_slug: string | null;
  last_message: string | null;
  last_message_at: string | null;
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
