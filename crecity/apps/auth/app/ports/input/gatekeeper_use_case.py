from __future__ import annotations

from abc import ABC, abstractmethod

from auth.app.dtos.gatekeeper_dto import GatekeeperQuery, GatekeeperResponse


class GatekeeperUseCase(ABC):
    """인증 (auth) 유스케이스 — 회원 인증·계정 — 크리에이터/브랜드 계정 경계 담당."""

    @abstractmethod
    async def introduce_myself(self, query: GatekeeperQuery) -> GatekeeperResponse:
        """인증 (auth)의 자기소개 메소드."""
        ...
