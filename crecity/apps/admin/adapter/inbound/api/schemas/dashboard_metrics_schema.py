from __future__ import annotations

from dataclasses import asdict

from pydantic import BaseModel

from admin.app.dtos.dashboard_metrics_dto import DashboardMetricsResult


class DashboardMetricsResponseSchema(BaseModel):
    """운영 대시보드 지표 응답(갭 #55) — 필드는 DTO와 1:1."""

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

    @classmethod
    def from_result(cls, result: DashboardMetricsResult) -> DashboardMetricsResponseSchema:
        return cls(**asdict(result))
