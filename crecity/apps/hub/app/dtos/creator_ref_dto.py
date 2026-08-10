from dataclasses import dataclass


@dataclass(frozen=True)
class CreatorRef:
    """크리에이터 참조 요약(슬러그 → 계정) — review 등 소비(BOUNDARIES §5 크리에이터 요약 조회)."""

    creator_user_id: int
    slug: str
    name: str
