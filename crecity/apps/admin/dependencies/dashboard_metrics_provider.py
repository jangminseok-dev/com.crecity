from __future__ import annotations

from fastapi import Depends

from admin.app.ports.input.dashboard_metrics_use_case import DashboardMetricsUseCase
from admin.app.use_cases.dashboard_metrics_interactor import DashboardMetricsInteractor
from hub.app.ports.output.platform_metrics_port import (
    AccountMetricsPort,
    OrderMetricsPort,
    ProfileMetricsPort,
)
from hub.dependencies.platform_metrics_provider import (
    get_account_metrics_port,
    get_order_metrics_port,
    get_profile_metrics_port,
)


def get_dashboard_metrics_use_case(
    accounts: AccountMetricsPort = Depends(get_account_metrics_port),
    profiles: ProfileMetricsPort = Depends(get_profile_metrics_port),
    orders: OrderMetricsPort = Depends(get_order_metrics_port),
) -> DashboardMetricsUseCase:
    return DashboardMetricsInteractor(accounts=accounts, profiles=profiles, orders=orders)
