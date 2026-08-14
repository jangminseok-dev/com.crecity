from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class DashboardMetricsResult:
    """운영 대시보드 한 화면치 지표(갭 #55) — 세 스포크의 집계를 합친 결과.

    지표는 조회 시점 스냅샷이며 저장하지 않는다(새 테이블 없음).
    """

    total_users: int
    creator_users: int
    brand_users: int
    pending_review: int
    approved_profiles: int
    rejected_profiles: int
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
