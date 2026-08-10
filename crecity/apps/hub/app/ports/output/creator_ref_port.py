from __future__ import annotations

from abc import ABC, abstractmethod

from hub.app.dtos.creator_ref_dto import CreatorRef


class CreatorRefPort(ABC):
    """크리에이터 참조 조회 포트 — 구현은 creator가 제공하고 main.py가 조립한다."""

    @abstractmethod
    async def get_creator_by_slug(self, slug: str) -> CreatorRef | None:
        """슬러그로 크리에이터 참조를 돌려준다 — 없거나 소유 계정 없으면 None."""
        ...
