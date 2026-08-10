from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum


class AccountType(StrEnum):
    """계정 유형 — 동일 이메일로 크리에이터·브랜드 겸용 불가(collabstr-analysis §3.8).

    배타성은 users.email unique + 계정당 단일 account_type으로 보장된다.
    """

    CREATOR = "CREATOR"
    BRAND = "BRAND"


@dataclass(frozen=True, slots=True)
class User:
    """회원 도메인 엔티티 — 소셜 로그인으로만 생성된다(비밀번호 없음)."""

    id: int
    email: str
    name: str
    account_type: AccountType
    created_at: datetime | None = None
