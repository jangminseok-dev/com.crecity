from __future__ import annotations

import secrets

from auth.app.dtos.social_login_dto import (
    AuthenticatedUser,
    AuthorizeUrlQuery,
    AuthorizeUrlResult,
    SocialLoginCommand,
    SocialLoginResult,
)
from auth.app.exceptions import EmailNotProvidedError, UnsupportedProviderError
from auth.app.ports.input.social_login_use_case import SocialLoginUseCase
from auth.app.ports.output.access_token_issuer import AccessTokenIssuer
from auth.app.ports.output.refresh_token_store import RefreshTokenStore
from auth.app.ports.output.role_repository import RoleRepository
from auth.app.ports.output.social_identity_repository import SocialIdentityRepository
from auth.app.ports.output.social_profile_gateway import SocialProfileGateway
from auth.app.ports.output.user_repository import UserRepository
from auth.domain.entities.social_identity_entity import SocialProvider
from auth.domain.entities.user_entity import AccountType, User


def _parse_account_type(raw: str) -> AccountType:
    try:
        return AccountType(raw)
    except ValueError:
        allowed = ", ".join(t.value for t in AccountType)
        raise ValueError(f"지원하지 않는 계정 유형입니다: {raw} (허용: {allowed})")


class SocialLoginInteractor(SocialLoginUseCase):

    def __init__(
        self,
        gateways: dict[SocialProvider, SocialProfileGateway],
        users: UserRepository,
        identities: SocialIdentityRepository,
        refresh_tokens: RefreshTokenStore,
        access_tokens: AccessTokenIssuer,
        roles: RoleRepository,
        refresh_ttl_seconds: int,
    ) -> None:
        self._gateways = gateways
        self._users = users
        self._identities = identities
        self._refresh_tokens = refresh_tokens
        self._access_tokens = access_tokens
        self._roles = roles
        self._refresh_ttl_seconds = refresh_ttl_seconds

    def _resolve(self, raw_provider: str) -> tuple[SocialProvider, SocialProfileGateway]:
        try:
            provider = SocialProvider(raw_provider.upper())
        except ValueError:
            provider = None
        if provider is None or provider not in self._gateways:
            allowed = ", ".join(p.value.lower() for p in self._gateways)
            raise UnsupportedProviderError(
                f"지원하지 않는 제공자입니다: {raw_provider} (허용: {allowed})"
            )
        return provider, self._gateways[provider]

    def authorize_url(self, query: AuthorizeUrlQuery) -> AuthorizeUrlResult:
        _, gateway = self._resolve(query.provider)
        return AuthorizeUrlResult(
            authorize_url=gateway.authorize_url(query.redirect_uri, query.state)
        )

    async def login(self, command: SocialLoginCommand) -> SocialLoginResult:
        provider, gateway = self._resolve(command.provider)
        profile = await gateway.fetch_profile(command.code, command.redirect_uri, command.state)
        if not profile.email:
            raise EmailNotProvidedError(
                f"{provider.value.lower()} 계정에서 이메일을 받지 못했습니다 — 이메일 제공 동의가 필요합니다."
            )

        identity = await self._identities.find_by_provider_uid(
            provider, profile.provider_user_id
        )
        is_new_user = False
        if identity is not None:
            user = await self._users.find_by_id(identity.user_id)
            if user is None:  # FK가 보장하므로 정상 경로에선 불가능 — 데이터 손상 신호
                raise RuntimeError(f"소셜 연결이 가리키는 회원이 없습니다: user_id={identity.user_id}")
        else:
            # 같은 이메일이면 제공자가 달라도 기존 계정에 연결한다(계정 배타성 —
            # 이메일당 계정 1개, 유형은 최초 가입 시 결정).
            user = await self._users.find_by_email(profile.email)
            if user is None:
                account_type = _parse_account_type(command.account_type)
                user = await self._users.create(
                    email=profile.email, name=profile.name, account_type=account_type
                )
                is_new_user = True
            await self._identities.create(user.id, provider, profile.provider_user_id)

        return SocialLoginResult(
            access_token=self._access_tokens.issue(
                user,
                roles=await self._roles.roles_for_user(user.id),
                permissions=await self._roles.permissions_for_user(user.id),
            ),
            refresh_token=await self._issue_refresh_token(user),
            user=AuthenticatedUser(
                id=user.id,
                email=user.email,
                name=user.name,
                account_type=user.account_type.value,
            ),
            is_new_user=is_new_user,
        )

    async def _issue_refresh_token(self, user: User) -> str:
        refresh_token = secrets.token_urlsafe(48)
        await self._refresh_tokens.save(refresh_token, user.id, self._refresh_ttl_seconds)
        return refresh_token
