from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Price:
    """패키지 판매가(원) — 생성 시점에 양수를 강제하는 값 객체.

    가격 책정은 크리에이터 자율(collabstr 정책)이라 상한·최소 단위는 두지 않는다.
    """

    krw: int

    def __post_init__(self) -> None:
        if self.krw <= 0:
            raise ValueError("가격은 1원 이상이어야 합니다.")
