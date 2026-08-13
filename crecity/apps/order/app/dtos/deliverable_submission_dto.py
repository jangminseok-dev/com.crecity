from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from order.domain.entities.deliverable_entity import Deliverable


@dataclass(frozen=True)
class SubmitDeliverableFileCommand:
    order_id: int
    actor_user_id: int
    content: bytes
    content_type: str
    original_name: str


@dataclass(frozen=True)
class SubmitDeliverableLinkCommand:
    order_id: int
    actor_user_id: int
    url: str
    caption: str | None = None  # 게시물 본문 — 광고 표기 검수용(선택)


@dataclass(frozen=True)
class DeliverableListQuery:
    order_id: int
    requester_user_id: int


@dataclass(frozen=True)
class DeliverableResult:
    id: int
    order_id: int
    kind: str
    file_name: str | None
    original_name: str | None
    url: str | None
    caption: str | None
    ad_disclosure_ok: bool | None  # 링크 납품물만 판정(파일은 None)
    created_at: datetime | None

    @classmethod
    def from_deliverable(cls, deliverable: Deliverable) -> DeliverableResult:
        return cls(
            id=deliverable.id,
            order_id=deliverable.order_id,
            kind=deliverable.kind.value,
            file_name=deliverable.file_name,
            original_name=deliverable.original_name,
            url=deliverable.url,
            caption=deliverable.caption,
            ad_disclosure_ok=deliverable.ad_disclosure_ok,
            created_at=deliverable.created_at,
        )
