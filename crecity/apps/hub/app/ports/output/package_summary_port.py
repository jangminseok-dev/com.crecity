from __future__ import annotations

from abc import ABC, abstractmethod

from hub.app.dtos.package_summary_dto import PackageSummary


class PackageSummaryPort(ABC):
    """패키지 요약 조회 포트 — 구현은 creator가 제공하고 main.py가 조립한다."""

    @abstractmethod
    async def get_package_summary(self, package_id: int) -> PackageSummary | None:
        """패키지 요약을 돌려준다 — 없거나 소유 계정이 없는 패키지(주문 불가)면 None."""
        ...
