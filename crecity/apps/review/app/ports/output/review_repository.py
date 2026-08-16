from __future__ import annotations

from abc import ABC, abstractmethod

from hub.app.dtos.outbox_event_dto import OutboxEvent
from review.domain.entities.review_entity import Review


class ReviewRepository(ABC):
    """리뷰 영속성 포트 (도메인어 명명 예외) — 평점·본문은 작성 전용, 답글만 1회 기록한다."""

    @abstractmethod
    async def create(
        self,
        order_id: int,
        brand_user_id: int,
        creator_user_id: int,
        communication_score: int,
        timeliness_score: int,
        satisfaction_score: int,
        comment: str,
        events: list[OutboxEvent] | None = None,
    ) -> Review: ...

    @abstractmethod
    async def find_by_order_id(self, order_id: int) -> Review | None: ...

    @abstractmethod
    async def find_by_id(self, review_id: int) -> Review | None: ...

    @abstractmethod
    async def save_reply(self, review_id: int, reply: str) -> Review | None:
        """크리에이터 답글 저장(갭 #53) — 대상 없으면 None. 자격·중복 검증은 도메인 몫."""
        ...

    @abstractmethod
    async def list_by_creator(self, creator_user_id: int) -> list[Review]:
        """크리에이터가 받은 리뷰 — 최신순."""
        ...
