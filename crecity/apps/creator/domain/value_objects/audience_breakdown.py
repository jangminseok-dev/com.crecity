from dataclasses import dataclass
from enum import StrEnum

# 비율은 퍼밀(‰) 정수로 다룬다 — 참여율(engagement_permille)과 같은 방식(부동소수 금지)
SHARE_MIN, SHARE_MAX = 1, 1000


class AudienceDimension(StrEnum):
    """오디언스 분해 축(§2.1-6) — 자가입력이라 축과 구간을 고정해 비교 가능하게 만든다."""

    AGE = "AGE"
    GENDER = "GENDER"


AGE_BUCKETS: tuple[str, ...] = ("10s", "20s", "30s", "40s", "50s+")
GENDER_BUCKETS: tuple[str, ...] = ("FEMALE", "MALE", "OTHER")

BUCKETS: dict[AudienceDimension, tuple[str, ...]] = {
    AudienceDimension.AGE: AGE_BUCKETS,
    AudienceDimension.GENDER: GENDER_BUCKETS,
}


class InvalidAudienceShareError(Exception):
    """구간·비율 규칙 위반 — 라우터에서 422로 변환."""


@dataclass(frozen=True, slots=True)
class AudienceShare:
    """한 구간의 비율 — (축, 구간)당 하나."""

    dimension: AudienceDimension
    bucket: str
    share_permille: int

    def __post_init__(self) -> None:
        allowed = BUCKETS[self.dimension]
        if self.bucket not in allowed:
            raise InvalidAudienceShareError(
                f"{self.dimension.value}의 구간이 아닙니다: {self.bucket} (허용: {', '.join(allowed)})"
            )
        if not SHARE_MIN <= self.share_permille <= SHARE_MAX:
            raise InvalidAudienceShareError("비율은 0.1%~100% 사이여야 합니다.")


def validate_breakdown(shares: list[AudienceShare]) -> list[AudienceShare]:
    """같은 축의 합이 100%를 넘지 않아야 한다 — 넘으면 입력을 잘못 본 것이다.

    100%에 못 미치는 것은 허용한다(상위 구간만 적는 경우가 흔하다).
    """
    seen: set[tuple[str, str]] = set()
    totals: dict[AudienceDimension, int] = {}
    for share in shares:
        key = (share.dimension.value, share.bucket)
        if key in seen:
            raise InvalidAudienceShareError(f"같은 구간이 두 번 들어왔습니다: {share.bucket}")
        seen.add(key)
        totals[share.dimension] = totals.get(share.dimension, 0) + share.share_permille
    for dimension, total in totals.items():
        if total > SHARE_MAX:
            raise InvalidAudienceShareError(
                f"{dimension.value} 비율 합이 100%를 넘습니다({total / 10:.1f}%)."
            )
    return shares
