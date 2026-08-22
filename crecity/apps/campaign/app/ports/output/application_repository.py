from __future__ import annotations

from abc import ABC, abstractmethod

from campaign.domain.entities.campaign_entity import CampaignApplication
from hub.app.dtos.outbox_event_dto import OutboxEvent
from campaign.domain.value_objects.application_sort import ApplicationSort


class ApplicationRepository(ABC):
    """지원서 영속성 포트."""

    @abstractmethod
    async def create(
        self,
        campaign_id: int,
        creator_user_id: int,
        message: str,
        proposed_price_krw: int,
        events: list[OutboxEvent] | None = None,
    ) -> CampaignApplication:
        """지원서와 알림 이벤트(갭 #73)를 같은 트랜잭션으로 적재한다."""
        ...

    @abstractmethod
    async def exists(self, campaign_id: int, creator_user_id: int) -> bool: ...

    @abstractmethod
    async def list_by_campaign(
        self,
        campaign_id: int,
        sort: ApplicationSort = ApplicationSort.OLDEST,
        only_open: bool = False,
    ) -> list[CampaignApplication]:
        """공고의 지원서 — 기본은 오래된 순. only_open이면 아직 수락되지 않은 것만(갭 #70)."""
        ...

    @abstractmethod
    async def list_by_creator(self, creator_user_id: int) -> list[CampaignApplication]:
        """크리에이터 본인의 지원 — 최신순(갭 #103)."""
        ...

    @abstractmethod
    async def find_by_id(self, application_id: int) -> CampaignApplication | None: ...

    @abstractmethod
    async def mark_paid(self, application_id: int, order_id: int) -> None:
        """수락(결제) 완료 표시 — 생성된 주문 id를 기록해 재결제를 차단한다."""
        ...
