// 백엔드 응답 타입 — 필드명은 백엔드(snake_case) 그대로, 변환하지 않는다(루트 CLAUDE.md 규칙).

export type ProfileListingItem = {
  id: number;
  slug: string;
  name: string;
  tagline: string;
  location: string | null;
  primary_category: string;
  created_at: string | null;
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

export type CreatorPackage = {
  id: number;
  profile_id: number;
  platform: "INSTAGRAM" | "YOUTUBE" | "TIKTOK" | "NAVER_BLOG" | "UGC";
  title: string;
  description: string;
  price_krw: number;
  created_at: string | null;
};
