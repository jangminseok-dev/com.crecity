from __future__ import annotations

from abc import ABC, abstractmethod

from admin.app.dtos.dashboard_metrics_dto import DashboardMetricsResult


class DashboardMetricsUseCase(ABC):
    """운영 대시보드 지표 조회(갭 #55) — 가입·심사·거래·정산 현황을 한 번에 본다."""

    @abstractmethod
    async def get_metrics(self) -> DashboardMetricsResult: ...
