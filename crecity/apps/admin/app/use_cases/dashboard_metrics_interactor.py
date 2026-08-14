from __future__ import annotations

import asyncio

from admin.app.dtos.dashboard_metrics_dto import DashboardMetricsResult
from admin.app.ports.input.dashboard_metrics_use_case import DashboardMetricsUseCase
from hub.app.ports.output.platform_metrics_port import (
    AccountMetricsPort,
    OrderMetricsPort,
    ProfileMetricsPort,
)


class DashboardMetricsInteractor(DashboardMetricsUseCase):
    """세 스포크의 집계를 합친다 — admin은 남의 테이블을 모르고 허브 계약만 소비한다."""

    def __init__(
        self,
        accounts: AccountMetricsPort,
        profiles: ProfileMetricsPort,
        orders: OrderMetricsPort,
    ) -> None:
        self._accounts = accounts
        self._profiles = profiles
        self._orders = orders

    async def get_metrics(self) -> DashboardMetricsResult:
        # 서로 의존이 없는 세 조회 — 순차로 기다릴 이유가 없다
        accounts, profiles, orders = await asyncio.gather(
            self._accounts.get_account_metrics(),
            self._profiles.get_profile_metrics(),
            self._orders.get_order_metrics(),
        )
        return DashboardMetricsResult(
            total_users=accounts.total_users,
            creator_users=accounts.creator_users,
            brand_users=accounts.brand_users,
            pending_review=profiles.pending_review,
            approved_profiles=profiles.approved,
            rejected_profiles=profiles.rejected,
            pending_accept=orders.pending_accept,
            in_progress=orders.in_progress,
            in_review=orders.in_review,
            completed=orders.completed,
            refunded=orders.refunded,
            cancelled=orders.cancelled,
            gmv_krw=orders.gmv_krw,
            platform_revenue_krw=orders.platform_revenue_krw,
            open_disputes=orders.open_disputes,
            pending_withdrawals=orders.pending_withdrawals,
            pending_withdrawal_krw=orders.pending_withdrawal_krw,
        )
