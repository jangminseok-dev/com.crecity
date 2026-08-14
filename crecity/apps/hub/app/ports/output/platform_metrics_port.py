from __future__ import annotations

from abc import ABC, abstractmethod

from hub.app.dtos.platform_metrics_dto import AccountMetrics, OrderMetrics, ProfileMetrics


class AccountMetricsPort(ABC):
    """가입 집계 포트 — 구현은 auth가 제공한다(운영 대시보드, 갭 #55)."""

    @abstractmethod
    async def get_account_metrics(self) -> AccountMetrics: ...


class ProfileMetricsPort(ABC):
    """프로필 심사 집계 포트 — 구현은 creator가 제공한다."""

    @abstractmethod
    async def get_profile_metrics(self) -> ProfileMetrics: ...


class OrderMetricsPort(ABC):
    """거래·정산 집계 포트 — 구현은 order가 제공한다.

    지표마다 소유 스포크가 다르므로 포트를 쪼갠다 — 한 포트를 여러 스포크가
    구현할 수 없고, 그렇게 묶으면 허브가 특정 스포크를 알게 된다.
    """

    @abstractmethod
    async def get_order_metrics(self) -> OrderMetrics: ...
