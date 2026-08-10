from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class OfferCreationCommand:

    conversation_id: int
    title: str
    price_krw: int
    requester_user_id: int  # 해당 대화의 크리에이터만 제안 가능


@dataclass(frozen=True)
class OffersQuery:

    conversation_id: int
    requester_user_id: int  # 당사자만 열람


@dataclass(frozen=True)
class OfferResult:

    id: int
    conversation_id: int
    title: str
    price_krw: int
    status: str
    order_id: int | None
    created_at: datetime | None
