import pytest

from auth.adapter.outbound.hub.jwt_access_token_verifier import JwtAccessTokenVerifier
from auth.adapter.outbound.jwt_access_token_issuer import JwtAccessTokenIssuer
from auth.domain.entities.user_entity import AccountType, User
from hub.app.exceptions import InvalidAccessTokenError

_SECRET = "test-secret"
_USER = User(id=7, email="kim@example.com", name="김뷰티", account_type=AccountType.CREATOR)


class _StubRevocationStore:
    def __init__(self, revoked=()):
        self.revoked = set(revoked)

    async def revoke(self, user_id, ttl_seconds):
        self.revoked.add(user_id)

    async def is_revoked(self, user_id):
        return user_id in self.revoked


def _token() -> str:
    return JwtAccessTokenIssuer(secret=_SECRET, ttl_seconds=60).issue(_USER, ["admin"], ["x.y"])


async def test_유효한_토큰은_주인과_권한을_돌려준다():
    verifier = JwtAccessTokenVerifier(secret=_SECRET, revocations=_StubRevocationStore())
    user = await verifier.verify(_token())
    assert (user.id, user.email, user.account_type) == (7, "kim@example.com", "CREATOR")
    assert user.roles == ("admin",) and user.permissions == ("x.y",)


async def test_탈퇴한_계정의_토큰은_서명이_유효해도_거부된다():
    verifier = JwtAccessTokenVerifier(secret=_SECRET, revocations=_StubRevocationStore([7]))
    with pytest.raises(InvalidAccessTokenError, match="탈퇴"):
        await verifier.verify(_token())


async def test_다른_시크릿으로_서명된_토큰은_거부된다():
    verifier = JwtAccessTokenVerifier(secret="other", revocations=_StubRevocationStore())
    with pytest.raises(InvalidAccessTokenError):
        await verifier.verify(_token())
