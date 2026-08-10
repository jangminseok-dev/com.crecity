import type { CreatorPackage } from "@/lib/types";

export const PLATFORM_LABELS: Record<CreatorPackage["platform"], string> = {
  INSTAGRAM: "인스타그램",
  YOUTUBE: "유튜브",
  TIKTOK: "틱톡",
  NAVER_BLOG: "네이버 블로그",
  UGC: "UGC",
};

const krwFormatter = new Intl.NumberFormat("ko-KR");

export function formatKrw(amount: number): string {
  return `${krwFormatter.format(amount)}원`;
}
