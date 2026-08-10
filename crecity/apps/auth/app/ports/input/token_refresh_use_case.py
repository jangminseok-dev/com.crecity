from __future__ import annotations

from abc import ABC, abstractmethod

from auth.app.dtos.token_refresh_dto import TokenRefreshCommand, TokenRefreshResult


class TokenRefreshUseCase(ABC):
    """토큰 갱신 유스케이스 — 리프레시 토큰은 1회용(회전식).

    사용한 토큰은 즉시 소멸하고 새 쌍을 발급한다 — 탈취 토큰의 재사용을 차단한다.
    """

    @abstractmethod
    async def refresh(self, command: TokenRefreshCommand) -> TokenRefreshResult:
        """리프레시 토큰을 소비하고 새 액세스·리프레시 토큰 쌍을 발급한다.

        Raises:
            InvalidRefreshTokenError: 무효·만료·재사용된 토큰.
        """
        ...
