from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from creator.domain.entities.profile_faq_entity import ProfileFaq


@dataclass(frozen=True)
class AddFaqCommand:

    requester_user_id: int
    question: str
    answer: str


@dataclass(frozen=True)
class RemoveFaqCommand:

    requester_user_id: int
    faq_id: int


@dataclass(frozen=True)
class FaqResult:

    id: int
    question: str
    answer: str
    created_at: datetime | None

    @classmethod
    def from_entity(cls, faq: ProfileFaq) -> FaqResult:
        return cls(
            id=faq.id, question=faq.question, answer=faq.answer, created_at=faq.created_at
        )
