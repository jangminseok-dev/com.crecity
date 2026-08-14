from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum

REASON_MIN_LENGTH, REASON_MAX_LENGTH = 10, 2000


class ReportTargetType(StrEnum):
    """신고 대상 — 주문 밖 어뷰징 경로(갭 #54).

    주문 안에서 벌어진 다툼은 분쟁(order `dispute`)이 다룬다 — 여기는 그 밖의 일이다.
    대상 id는 타 스포크 논리 참조(DB FK 없음).
    """

    PROFILE = "PROFILE"  # 크리에이터 프로필(profile_id)
    CONVERSATION = "CONVERSATION"  # 채팅 대화방(conversation_id)


class ReportStatus(StrEnum):
    OPEN = "OPEN"
    RESOLVED = "RESOLVED"


class InvalidReasonError(Exception):
    """신고 사유 길이 위반 — 라우터에서 422로 변환."""


class ReportAlreadyResolvedError(Exception):
    """이미 처리된 신고 — 라우터에서 409로 변환."""


def validate_reason(reason: str) -> str:
    """사유는 운영자가 판단할 수 있을 만큼은 적어야 한다(장난 신고 억제)."""
    text = reason.strip()
    if not REASON_MIN_LENGTH <= len(text) <= REASON_MAX_LENGTH:
        raise InvalidReasonError(
            f"신고 사유는 {REASON_MIN_LENGTH}~{REASON_MAX_LENGTH}자로 적어 주세요."
        )
    return text


@dataclass(frozen=True, slots=True)
class Report:
    """어뷰징 신고 — 접수는 로그인 사용자, 처리는 운영자."""

    id: int
    reporter_user_id: int
    target_type: ReportTargetType
    target_id: int
    reason: str
    status: ReportStatus
    resolution_note: str = ""
    resolved_by_user_id: int | None = None
    created_at: datetime | None = None
    resolved_at: datetime | None = None

    def ensure_can_resolve(self) -> None:
        if self.status is ReportStatus.RESOLVED:
            raise ReportAlreadyResolvedError("이미 처리된 신고입니다.")
