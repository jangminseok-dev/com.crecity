from __future__ import annotations

from abc import ABC, abstractmethod

from auth.app.dtos.social_login_dto import (
    AuthorizeUrlQuery,
    AuthorizeUrlResult,
    SocialLoginCommand,
    SocialLoginResult,
)


class SocialLoginUseCase(ABC):
    """소셜 로그인 유스케이스 — 카카오·네이버·구글 (collabstr-analysis §3.8).

    플로우: 프론트가 authorize_url로 이동 → 제공자 콜백으로 받은 code를
    login에 전달 → 가입(첫 로그인) 또는 로그인 후 토큰 쌍 발급.
    같은 이메일이면 제공자가 달라도 한 계정에 연결된다(계정 배타성).
    """

    @abstractmethod
    def authorize_url(self, query: AuthorizeUrlQuery) -> AuthorizeUrlResult:
        """제공자 인가 페이지 URL을 조립한다 (CPU-bound).

        Raises:
            UnsupportedProviderError: 지원하지 않는 제공자.
        """
        ...

    @abstractmethod
    async def login(self, command: SocialLoginCommand) -> SocialLoginResult:
        """인가 코드를 교환해 로그인(필요 시 가입)하고 토큰 쌍을 발급한다.

        Raises:
            UnsupportedProviderError: 지원하지 않는 제공자.
            OAuthExchangeError: 제공자와의 교환 실패.
            EmailNotProvidedError: 제공자가 이메일을 주지 않음.
            ValueError: account_type이 CREATOR/BRAND가 아님.
        """
        ...
