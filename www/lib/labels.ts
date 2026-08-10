import type { CreatorPackage } from "@/lib/types";

export const PLATFORM_LABELS: Record<CreatorPackage["platform"], string> = {
  INSTAGRAM: "인스타그램",
  YOUTUBE: "유튜브",
  TIKTOK: "틱톡",
  NAVER_BLOG: "네이버 블로그",
  UGC: "UGC",
};

export const PROFILE_STATUS_LABELS: Record<string, string> = {
  PENDING: "심사 대기",
  APPROVED: "승인됨",
  REJECTED: "반려됨",
};

const krwFormatter = new Intl.NumberFormat("ko-KR");

export function formatKrw(amount: number): string {
  return `${krwFormatter.format(amount)}원`;
}
