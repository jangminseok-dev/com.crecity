from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

# 3축 평점(collabstr §2.1) — 소통 / 기한 준수 / 만족도, 각 1~5점
SCORE_MIN, SCORE_MAX = 1, 5


class InvalidScoreError(Exception):
    """평점 범위(1~5) 위반 — 라우터에서 422로 변환."""


class ReplyNotAllowedError(Exception):
    """답글 작성 자격 없음(대상 크리에이터 아님) — 라우터에서 403으로 변환."""


class ReplyAlreadyExistsError(Exception):
    """이미 답글이 있음 — 라우터에서 409로 변환."""


def validate_score(name: str, value: int) -> int:
    if not SCORE_MIN <= value <= SCORE_MAX:
        raise InvalidScoreError(f"{name} 평점은 {SCORE_MIN}~{SCORE_MAX} 사이여야 합니다.")
    return value


@dataclass(frozen=True, slots=True)
class Review:
    """리뷰 도메인 엔티티 — 완료 주문당 1개, 브랜드가 작성한다.

    order_id·user_id들은 타 스포크 논리 참조(스포크 경계 — DB FK 없음).
    """

    id: int
    order_id: int
    brand_user_id: int  # 작성자
    creator_user_id: int  # 대상 크리에이터
    communication_score: int
    timeliness_score: int
    satisfaction_score: int
    comment: str
    created_at: datetime | None = None
    # 크리에이터 답글(갭 #53) — 리뷰당 1개, 없으면 빈 문자열
    reply: str = ""
    replied_at: datetime | None = None

    def overall_score(self) -> float:
        """종합 평점 = 3축 평균 (소수 1자리)."""
        return round(
            (self.communication_score + self.timeliness_score + self.satisfaction_score) / 3, 1
        )

    def ensure_can_reply(self, actor_user_id: int) -> None:
        """답글 자격 검증 — 대상 크리에이터 본인만, 리뷰당 1회.

        리뷰가 수정·삭제되지 않는 것과 같은 이유로 답글도 되돌리지 않는다
        (평판 기록은 사후에 흔들리지 않아야 한다).
        """
        if actor_user_id != self.creator_user_id:
            raise ReplyNotAllowedError("리뷰를 받은 크리에이터만 답글을 남길 수 있습니다.")
        if self.reply:
            raise ReplyAlreadyExistsError("이미 답글을 남긴 리뷰입니다.")
