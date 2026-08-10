from __future__ import annotations

from abc import ABC, abstractmethod

from hub.app.dtos.verified_user_dto import VerifiedUser


class AccessTokenVerifier(ABC):
    """액세스 토큰 검증 포트 — 구현은 auth가 제공하고 main.py가 조립한다.

    스포크는 이 포트(허브 계약)만 보고 '현재 사용자'를 얻는다 —
    auth를 직접 import하면 스포크 상호 독립 위반.
    """

    @abstractmethod
    def verify(self, token: str) -> VerifiedUser:
        """서명·만료를 검증하고 토큰 주인을 돌려준다 (CPU-bound).

        Raises:
            InvalidAccessTokenError: 무효·만료·위조 토큰.
        """
        ...
