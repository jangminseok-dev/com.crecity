from __future__ import annotations

from auth.app.dtos.logout_dto import LogoutCommand
from auth.app.ports.input.logout_use_case import LogoutUseCase
from auth.app.ports.output.refresh_token_store import RefreshTokenStore


class LogoutInteractor(LogoutUseCase):

    def __init__(self, refresh_tokens: RefreshTokenStore) -> None:
        self._refresh_tokens = refresh_tokens

    async def logout(self, command: LogoutCommand) -> None:
        # pop(GETDEL)이 곧 폐기다 — 없는 토큰(이미 회전·만료)이어도 멱등하게 성공
        await self._refresh_tokens.pop(command.refresh_token)
