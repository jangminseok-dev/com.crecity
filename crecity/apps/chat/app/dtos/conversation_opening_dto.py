from dataclasses import dataclass


@dataclass(frozen=True)
class OpenConversationCommand:
    """브랜드가 크리에이터에게 문의를 시작한다 — 쌍당 1개(있으면 재사용)."""

    creator_slug: str
    brand_user_id: int
    account_type: str  # BRAND만
