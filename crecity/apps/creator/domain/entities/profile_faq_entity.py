from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

# 프로필당 FAQ 상한 — 아코디언이 길어지면 오히려 읽히지 않는다(§2.1-9)
MAX_FAQ_PER_PROFILE = 10


@dataclass(frozen=True, slots=True)
class ProfileFaq:
    """프로필 FAQ — 크리에이터가 직접 쓰는 자주 묻는 질문(오디언스·협업 이력 등)."""

    id: int
    profile_id: int
    question: str
    answer: str
    created_at: datetime | None = None
