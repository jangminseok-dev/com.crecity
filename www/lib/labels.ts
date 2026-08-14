import type { CreatorPackage, Order } from "@/lib/types";

export const PLATFORM_LABELS: Record<CreatorPackage["platform"], string> = {
  INSTAGRAM: "인스타그램",
  YOUTUBE: "유튜브",
  TIKTOK: "틱톡",
  NAVER_BLOG: "네이버 블로그",
  UGC: "UGC",
};

/* 목록 정렬 기준 — 백엔드 creator/domain/value_objects/profile_sort.py와 1:1.
   평점·인기순은 다른 스포크 데이터라 DB 정렬 불가(인기순은 별도 섹션이 담당). */
export const PROFILE_SORTS = [
  { value: "latest", label: "최신순" },
  { value: "price_asc", label: "가격 낮은순" },
  { value: "price_desc", label: "가격 높은순" },
] as const;

export type ProfileSort = (typeof PROFILE_SORTS)[number]["value"];

/** 허용 목록 밖 값은 기본값으로 — URL을 손으로 고쳐도 백엔드 422를 만들지 않는다. */
export function toProfileSort(value?: string): ProfileSort {
  return PROFILE_SORTS.some((sort) => sort.value === value)
    ? (value as ProfileSort)
    : "latest";
}

/* 고정 카테고리 목록 — 백엔드 creator/domain/value_objects/category.py와 1:1 */
export const CREATOR_CATEGORIES = [
  "뷰티",
  "패션",
  "푸드",
  "여행",
  "테크",
  "피트니스",
  "라이프",
  "포토",
  "영상",
] as const;

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

/** 팔로워 수 축약 표기 — 12500 → "1.3만", 980 → "980" */
export function formatFollowers(count: number): string {
  if (count >= 10000) {
    const man = count / 10000;
    return `${man >= 100 ? Math.round(man) : Math.round(man * 10) / 10}만`;
  }
  return krwFormatter.format(count);
}
