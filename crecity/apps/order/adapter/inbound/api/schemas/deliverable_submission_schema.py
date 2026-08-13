from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel

from order.app.dtos.deliverable_submission_dto import DeliverableResult


class DeliverableLinkRequestSchema(BaseModel):
    url: str
    caption: str | None = None  # 게시물 본문 — 광고 표기 검수용(선택)


class DeliverableResponseSchema(BaseModel):
    id: int
    order_id: int
    kind: str  # FILE | LINK
    file_url: str | None  # kind=FILE — /uploads/deliverables/{저장 파일명}
    original_name: str | None
    url: str | None  # kind=LINK
    caption: str | None
    ad_disclosure_ok: bool | None  # 광고 표기 검수 — 링크만 판정(파일은 null)
    created_at: datetime | None

    @classmethod
    def from_result(cls, result: DeliverableResult) -> DeliverableResponseSchema:
        return cls(
            id=result.id,
            order_id=result.order_id,
            kind=result.kind,
            file_url=(
                f"/uploads/deliverables/{result.file_name}" if result.file_name else None
            ),
            original_name=result.original_name,
            url=result.url,
            caption=result.caption,
            ad_disclosure_ok=result.ad_disclosure_ok,
            created_at=result.created_at,
        )
