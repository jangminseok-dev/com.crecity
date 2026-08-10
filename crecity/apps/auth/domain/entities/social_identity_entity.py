from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum


class SocialProvider(StrEnum):
    """지원하는 OAuth 제공자."""

    KAKAO = "KAKAO"
    NAVER = "NAVER"
    GOOGLE = "GOOGLE"


@dataclass(frozen=True, slots=True)
class SocialIdentity:
    """소셜 계정 연결 — 한 회원(users)에 제공자별 계정을 잇는다(3NF 분리).

    (provider, provider_user_id)가 유일해야 한다 — 같은 카카오 계정이
    두 회원에 연결될 수 없다.
    """

    id: int
    user_id: int
    provider: SocialProvider
    provider_user_id: str
    created_at: datetime | None = None
