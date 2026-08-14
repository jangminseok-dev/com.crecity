from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class AccountMetrics:
    """가입 계정 집계 — auth가 채운다(탈퇴 계정 제외)."""

    total_users: int
    creator_users: int
    brand_users: int


@dataclass(frozen=True, slots=True)
class ProfileMetrics:
    """크리에이터 프로필 심사 현황 — creator가 채운다."""

    pending_review: int
    approved: int
    rejected: int


@dataclass(frozen=True, slots=True)
class OrderMetrics:
    """거래·정산 현황 — order가 채운다(원장이 진실의 원천).

    gmv_krw는 성사된 거래액(COMPLETED 주문 금액 합), platform_revenue_krw는
    원장의 PLATFORM_REVENUE 기입 합이다 — 수수료 계산을 여기서 다시 하지 않는다.
    """

    pending_accept: int
    in_progress: int
    in_review: int
    completed: int
    refunded: int
    cancelled: int
    gmv_krw: int
    platform_revenue_krw: int
    open_disputes: int
    pending_withdrawals: int
    pending_withdrawal_krw: int
