import pytest

from auth.app.dtos.social_login_dto import (
    AuthorizeUrlQuery,
    SocialLoginCommand,
    SocialProfile,
)
from auth.app.exceptions import EmailNotProvidedError, UnsupportedProviderError
from auth.app.use_cases.social_login_interactor import SocialLoginInteractor
from auth.domain.entities.social_identity_entity import SocialIdentity, SocialProvider
from auth.domain.entities.user_entity import AccountType, User


class _StubGateway:
    def __init__(self, profile: SocialProfile):
        self.profile = profile

    def authorize_url(self, redirect_uri, state):
        return f"https://provider.example/authorize?redirect_uri={redirect_uri}&state={state}"

    async def fetch_profile(self, code, redirect_uri, state):
        return self.profile


class _StubUserRepository:
    def __init__(self, users: list[User] | None = None):
        self.users = list(users or [])

    async def create(self, email, name, account_type):
        user = User(id=len(self.users) + 1, email=email, name=name, account_type=account_type)
        self.users.append(user)
        return user

    async def find_by_id(self, user_id):
        return next((u for u in self.users if u.id == user_id), None)

    async def find_by_email(self, email):
        return next((u for u in self.users if u.email == email), None)


class _StubIdentityRepository:
    def __init__(self, identities: list[SocialIdentity] | None = None):
        self.identities = list(identities or [])

    async def create(self, user_id, provider, provider_user_id):
        identity = SocialIdentity(
            id=len(self.identities) + 1,
            user_id=user_id,
            provider=provider,
            provider_user_id=provider_user_id,
        )
        self.identities.append(identity)
        return identity

    async def find_by_provider_uid(self, provider, provider_user_id):
        return next(
            (
                i
                for i in self.identities
                if i.provider == provider and i.provider_user_id == provider_user_id
            ),
            None,
        )


class _StubRefreshTokenStore:
    def __init__(self):
        self.saved: dict[str, int] = {}

    async def save(self, token, user_id, ttl_seconds):
        self.saved[token] = user_id

    async def pop(self, token):
        return self.saved.pop(token, None)


class _StubAccessTokenIssuer:
    def issue(self, user):
        return f"access-{user.id}"


def _interactor(
    profile=None,
    users=None,
    identities=None,
    refresh_store=None,
):
    profile = profile or SocialProfile(
        provider_user_id="kakao-1", email="kim@example.com", name="김뷰티"
    )
    return SocialLoginInteractor(
        gateways={SocialProvider.KAKAO: _StubGateway(profile)},
        users=users or _StubUserRepository(),
        identities=identities or _StubIdentityRepository(),
        refresh_tokens=refresh_store or _StubRefreshTokenStore(),
        access_tokens=_StubAccessTokenIssuer(),
        refresh_ttl_seconds=1209600,
    )


def _command(provider="kakao", account_type="CREATOR"):
    return SocialLoginCommand(
        provider=provider,
        code="auth-code",
        redirect_uri="http://localhost:3000/callback",
        state="csrf",
        account_type=account_type,
    )


async def test_첫_로그인이면_가입하고_토큰_쌍을_발급한다():
    users = _StubUserRepository()
    identities = _StubIdentityRepository()
    refresh_store = _StubRefreshTokenStore()
    interactor = _interactor(users=users, identities=identities, refresh_store=refresh_store)

    result = await interactor.login(_command(account_type="CREATOR"))

    assert result.is_new_user is True
    assert result.user.email == "kim@example.com"
    assert result.user.account_type == "CREATOR"
    assert result.access_token == "access-1"
    assert refresh_store.saved[result.refresh_token] == 1
    assert identities.identities[0].provider is SocialProvider.KAKAO


async def test_기존_연결이면_로그인만_한다():
    user = User(id=7, email="kim@example.com", name="김뷰티", account_type=AccountType.CREATOR)
    identity = SocialIdentity(
        id=1, user_id=7, provider=SocialProvider.KAKAO, provider_user_id="kakao-1"
    )
    identities = _StubIdentityRepository([identity])
    interactor = _interactor(users=_StubUserRepository([user]), identities=identities)

    result = await interactor.login(_command())

    assert result.is_new_user is False
    assert result.user.id == 7
    assert len(identities.identities) == 1  # 새 연결이 생기지 않는다


async def test_같은_이메일이면_다른_제공자도_기존_계정에_연결된다():
    user = User(id=7, email="kim@example.com", name="김뷰티", account_type=AccountType.BRAND)
    identities = _StubIdentityRepository()  # 카카오 연결은 아직 없음
    interactor = _interactor(users=_StubUserRepository([user]), identities=identities)

    result = await interactor.login(_command(account_type="CREATOR"))

    assert result.is_new_user is False
    assert result.user.id == 7
    assert result.user.account_type == "BRAND"  # 요청 유형이 아니라 저장된 유형 유지(배타성)
    assert identities.identities[0].user_id == 7


async def test_이메일을_받지_못하면_EmailNotProvidedError():
    profile = SocialProfile(provider_user_id="kakao-1", email=None, name="김뷰티")
    interactor = _interactor(profile=profile)
    with pytest.raises(EmailNotProvidedError):
        await interactor.login(_command())


async def test_지원하지_않는_제공자면_UnsupportedProviderError():
    interactor = _interactor()
    with pytest.raises(UnsupportedProviderError):
        await interactor.login(_command(provider="facebook"))


async def test_잘못된_계정_유형이면_ValueError():
    interactor = _interactor()
    with pytest.raises(ValueError):
        await interactor.login(_command(account_type="ADMIN"))


async def test_authorize_url은_게이트웨이에_위임한다():
    interactor = _interactor()
    result = interactor.authorize_url(
        AuthorizeUrlQuery(provider="kakao", redirect_uri="http://cb", state="csrf")
    )
    assert result.authorize_url == "https://provider.example/authorize?redirect_uri=http://cb&state=csrf"
