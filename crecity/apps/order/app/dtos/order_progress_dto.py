from dataclasses import dataclass


@dataclass(frozen=True)
class OrderTransitionCommand:
    """전이 공용 커맨드 — 행위자 권한 판정은 도메인(Order)이 한다."""

    order_id: int
    actor_user_id: int


@dataclass(frozen=True)
class RevisionRequestCommand:
    """수정 요청 커맨드(갭 #84) — 피드백 본문이 필수라 전이 공용 커맨드와 분리한다."""

    order_id: int
    actor_user_id: int
    comment: str
