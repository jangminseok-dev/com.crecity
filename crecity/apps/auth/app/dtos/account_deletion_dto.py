from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class DeleteAccountCommand:

    user_id: int
    refresh_token: str | None  # 있으면 함께 폐기(BFF가 쿠키에서 전달)
