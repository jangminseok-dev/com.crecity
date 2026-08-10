from __future__ import annotations

import secrets

from auth.app.dtos.token_refresh_dto import TokenRefreshCommand, TokenRefreshResult
from auth.app.exceptions import InvalidRefreshTokenError
from auth.app.ports.input.token_refresh_use_case import TokenRefreshUseCase
from auth.app.ports.output.access_token_issuer import AccessTokenIssuer
from auth.app.ports.output.refresh_token_store import RefreshTokenStore
from auth.app.ports.output.role_repository import RoleRepository
from auth.app.ports.output.user_repository import UserRepository


class TokenRefreshInteractor(TokenRefreshUseCase):

    def __init__(
        self,
        users: UserRepository,
        refresh_tokens: RefreshTokenStore,
        access_tokens: AccessTokenIssuer,
        roles: RoleRepository,
        refresh_ttl_seconds: int,
    ) -> None:
        self._users = users
        self._refresh_tokens = refresh_tokens
        self._access_tokens = access_tokens
        self._roles = roles
        self._refresh_ttl_seconds = refresh_ttl_seconds

    async def refresh(self, command: TokenRefreshCommand) -> TokenRefreshResult:
        user_id = await self._refresh_tokens.pop(command.refresh_token)
        if user_id is None:
            raise InvalidRefreshTokenError("유효하지 않은 리프레시 토큰입니다.")
        user = await self._users.find_by_id(user_id)
        if user is None:
            raise InvalidRefreshTokenError("탈퇴한 계정의 토큰입니다.")
        new_refresh_token = secrets.token_urlsafe(48)
        await self._refresh_tokens.save(new_refresh_token, user.id, self._refresh_ttl_seconds)
        return TokenRefreshResult(
            access_token=self._access_tokens.issue(
                user,
                roles=await self._roles.roles_for_user(user.id),
                permissions=await self._roles.permissions_for_user(user.id),
            ),
            refresh_token=new_refresh_token,
        )
