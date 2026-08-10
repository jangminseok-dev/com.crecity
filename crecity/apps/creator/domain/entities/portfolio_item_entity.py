from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class PortfolioItem:
    """포트폴리오 사진 1장 — creator_profiles에 종속."""

    id: int
    profile_id: int
    file_name: str  # 저장소 내 파일명(무작위 생성) — 원본 파일명은 보관하지 않는다
    created_at: datetime | None = None
