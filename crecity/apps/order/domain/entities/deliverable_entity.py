from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum

from order.domain.value_objects.ad_disclosure import has_ad_disclosure


class DeliverableKind(StrEnum):
    FILE = "FILE"
    LINK = "LINK"


@dataclass(frozen=True, slots=True)
class Deliverable:
    """납품물 — 크리에이터가 인도한 결과물(파일 또는 링크).

    append-only(수정·삭제 없음) — 에스크로 승인·분쟁 판단의 근거로 보존된다.
    kind=FILE이면 file_name·original_name, kind=LINK면 url이 채워진다.
    """

    id: int
    order_id: int
    kind: DeliverableKind
    file_name: str | None  # 저장 파일명(uuid) — /uploads/deliverables/{file_name}로 서빙
    original_name: str | None  # 업로드 당시 파일명(표시용)
    url: str | None
    caption: str | None = None  # 게시물 본문 — 광고 표기 검수 대상(갭 #17)
    created_at: datetime | None = None

    @property
    def ad_disclosure_ok(self) -> bool | None:
        """광고 표기 검수 결과 — 링크 납품물만 대상(파일은 본문이 없어 None)."""
        if self.kind is not DeliverableKind.LINK:
            return None
        return has_ad_disclosure(self.caption)
