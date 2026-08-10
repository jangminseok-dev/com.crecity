from __future__ import annotations

import re
from dataclasses import dataclass

# 소문자·숫자·하이픈, 3~30자, 하이픈으로 시작/끝 금지 — 크리에이터 고유 URL 단위(SEO).
_SLUG_PATTERN = re.compile(r"^[a-z0-9](?:[a-z0-9-]{1,28})[a-z0-9]$")


@dataclass(frozen=True, slots=True)
class Slug:
    """크리에이터 프로필 고유 슬러그 — 생성 시점에 형식을 강제하는 값 객체."""

    value: str

    def __post_init__(self) -> None:
        if not _SLUG_PATTERN.fullmatch(self.value):
            raise ValueError(
                "슬러그는 소문자·숫자·하이픈만으로 3~30자여야 하며, "
                "하이픈으로 시작하거나 끝날 수 없습니다."
            )
