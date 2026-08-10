import pytest

from auth.app.dtos.token_refresh_dto import TokenRefreshCommand
from auth.app.exceptions import InvalidRefreshTokenError
from auth.app.use_cases.token_refresh_interactor import TokenRefreshInteractor
from auth.domain.entities.user_entity import AccountType, User


class _StubUserRepository:
    def __init__(self, user: User | None = None):
        self.user = user

    async def create(self, email, name, account_type):
        raise NotImplementedError

    async def find_by_id(self, user_id):
        return self.user if self.user and self.user.id == user_id else None

    async def find_by_email(self, email):
        raise NotImplementedError


class _StubRefreshTokenStore:
    def __init__(self, tokens: dict[str, int] | None = None):
        self.tokens = dict(tokens or {})

    async def save(self, token, user_id, ttl_seconds):
        self.tokens[token] = user_id

    async def pop(self, token):
        return self.tokens.pop(token, None)


class _StubAccessTokenIssuer:
    def issue(self, user):
        return f"access-{user.id}"


def _user():
    return User(id=7, email="kim@example.com", name="김뷰티", account_type=AccountType.CREATOR)


async def test_유효한_토큰이면_새_쌍을_발급하고_기존_토큰은_소멸한다():
    store = _StubRefreshTokenStore({"old-refresh": 7})
    interactor = TokenRefreshInteractor(
        users=_StubUserRepository(_user()),
        refresh_tokens=store,
        access_tokens=_StubAccessTokenIssuer(),
        refresh_ttl_seconds=1209600,
    )

    result = await interactor.refresh(TokenRefreshCommand(refresh_token="old-refresh"))

    assert result.access_token == "access-7"
    assert result.refresh_token != "old-refresh"
    assert "old-refresh" not in store.tokens  # 회전 — 이전 토큰 재사용 불가
    assert store.tokens[result.refresh_token] == 7


async def test_무효한_토큰이면_InvalidRefreshTokenError():
    interactor = TokenRefreshInteractor(
        users=_StubUserRepository(_user()),
        refresh_tokens=_StubRefreshTokenStore(),
        access_tokens=_StubAccessTokenIssuer(),
        refresh_ttl_seconds=1209600,
    )
    with pytest.raises(InvalidRefreshTokenError):
        await interactor.refresh(TokenRefreshCommand(refresh_token="unknown"))


async def test_탈퇴한_계정의_토큰이면_InvalidRefreshTokenError():
    interactor = TokenRefreshInteractor(
        users=_StubUserRepository(user=None),
        refresh_tokens=_StubRefreshTokenStore({"orphan": 99}),
        access_tokens=_StubAccessTokenIssuer(),
        refresh_ttl_seconds=1209600,
    )
    with pytest.raises(InvalidRefreshTokenError):
        await interactor.refresh(TokenRefreshCommand(refresh_token="orphan"))
