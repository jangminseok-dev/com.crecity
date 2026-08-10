from __future__ import annotations

from abc import ABC, abstractmethod

from auth.app.dtos.social_login_dto import SocialProfile


class SocialProfileGateway(ABC):
    """OAuth 제공자 게이트웨이 — 제공자별 구현체(카카오·네이버·구글)가 뒤에 선다."""

    @abstractmethod
    def authorize_url(self, redirect_uri: str, state: str) -> str:
        """제공자 인가 페이지 URL을 조립한다."""
        ...

    @abstractmethod
    async def fetch_profile(self, code: str, redirect_uri: str, state: str) -> SocialProfile:
        """인가 코드를 액세스 토큰으로 교환하고 프로필을 조회한다.

        Raises:
            OAuthExchangeError: 교환·조회 실패(만료 코드, 설정 오류 등).
        """
        ...
