import type { CreatorPackage, Order } from "@/lib/types";

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

export const ORDER_STATUS_LABELS: Record<Order["status"], string> = {
  PENDING_ACCEPT: "수락 대기",
  IN_PROGRESS: "작업 중",
  IN_REVIEW: "검토 대기",
  COMPLETED: "완료",
  REFUNDED: "환불됨",
  CANCELLED: "취소됨",
};

/** 마감까지 남은 시간 — 지났으면 "곧 자동 처리" (주기 스캔이 전이). */
export function formatDeadline(deadlineAt: string): string {
  const remainingMs = new Date(deadlineAt).getTime() - Date.now();
  if (remainingMs <= 0) return "마감 경과 — 곧 자동 처리됩니다";
  const hours = Math.floor(remainingMs / 3_600_000);
  if (hours >= 24) return `${Math.floor(hours / 24)}일 ${hours % 24}시간 남음`;
  if (hours >= 1) return `${hours}시간 남음`;
  return `${Math.max(1, Math.floor(remainingMs / 60_000))}분 남음`;
}

const krwFormatter = new Intl.NumberFormat("ko-KR");

export function formatKrw(amount: number): string {
  return `${krwFormatter.format(amount)}원`;
}
