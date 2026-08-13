from dataclasses import dataclass

_MIN_LENGTH = 10
_MAX_LENGTH = 2000


@dataclass(frozen=True)
class DisputeReason:
    """분쟁 사유 검증 VO — 운영자가 판정하려면 최소한의 설명이 필요하다."""

    text: str

    def __post_init__(self) -> None:
        stripped = self.text.strip()
        if len(stripped) < _MIN_LENGTH:
            raise ValueError(f"분쟁 사유는 {_MIN_LENGTH}자 이상 적어 주세요.")
        if len(stripped) > _MAX_LENGTH:
            raise ValueError(f"분쟁 사유는 {_MAX_LENGTH}자 이하여야 합니다.")
        object.__setattr__(self, "text", stripped)
