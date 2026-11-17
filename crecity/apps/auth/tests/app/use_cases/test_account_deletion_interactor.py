import pytest

from auth.app.dtos.account_deletion_dto import DeleteAccountCommand
from auth.app.exceptions import (
    ActiveOrderExistsError,
    RemainingBalanceError,
    UserNotFoundError,
)
from auth.app.use_cases.account_deletion_interactor import AccountDeletionInteractor
from auth.domain.entities.user_entity import AccountType, User

USER_ID = 100
_USER = User(id=USER_ID, email="kim@example.com", name="김뷰티", account_type=AccountType.CREATOR)


class _StubUserRepository:
    def __init__(self, user):
        self.user = user
        self.deleted: list[tuple[int, str]] = []

    async def create(self, email, name, account_type):
        raise NotImplementedError

    async def find_by_id(self, user_id):
        return self.user if self.user and self.user.id == user_id else None

    async def find_by_email(self, email):
        raise NotImplementedError

    async def soft_delete(self, user_id, anonymized_email):
        self.deleted.append((user_id, anonymized_email))


class _StubIdentityRepository:
    def __init__(self):
        self.deleted: list[int] = []

    async def create(self, user_id, provider, provider_user_id):
        raise NotImplementedError

    async def find_by_provider_uid(self, provider, provider_user_id):
        raise NotImplementedError

    async def delete_by_user_id(self, user_id):
        self.deleted.append(user_id)


class _StubRefreshTokenStore:
    def __init__(self):
        self.popped: list[str] = []

    async def save(self, token, user_id, ttl_seconds):
        raise NotImplementedError

    async def pop(self, token):
        self.popped.append(token)
        return None


class _StubActiveOrderPort:
    def __init__(self, active=False):
        self.active = active

    async def has_active_orders(self, user_id):
        return self.active


class _StubBalancePort:
    def __init__(self, balance=0):
        self.balance = balance

    async def get_balance_krw(self, user_id):
        return self.balance


class _StubRevocationStore:
    def __init__(self):
        self.revoked: list[tuple[int, int]] = []

    async def revoke(self, user_id, ttl_seconds):
        self.revoked.append((user_id, ttl_seconds))

    async def is_revoked(self, user_id):
        return any(uid == user_id for uid, _ in self.revoked)


class _StubProfileDeactivationPort:
    def __init__(self):
        self.deactivated: list[int] = []

    async def deactivate_profile(self, user_id):
        self.deactivated.append(user_id)


def _interactor(user=_USER, active=False, balance=0):
    users = _StubUserRepository(user)
    identities = _StubIdentityRepository()
    tokens = _StubRefreshTokenStore()
    profiles = _StubProfileDeactivationPort()
    revocations = _StubRevocationStore()
    interactor = AccountDeletionInteractor(
        users=users,
        identities=identities,
        refresh_tokens=tokens,
        active_orders=_StubActiveOrderPort(active),
        balances=_StubBalancePort(balance),
        profiles=profiles,
        revocations=revocations,
        access_ttl_seconds=1800,
    )
    return interactor, users, identities, tokens, profiles, revocations


async def test_탈퇴하면_익명화되고_연결이_모두_정리된다():
    interactor, users, identities, tokens, profiles, revocations = _interactor()
    await interactor.delete(DeleteAccountCommand(user_id=USER_ID, refresh_token="tok"))

    assert users.deleted[0][0] == USER_ID
    assert "kim@example.com" not in users.deleted[0][1]  # 이메일 익명화
    assert identities.deleted == [USER_ID]  # 소셜 연결 해제(재가입 가능)
    assert profiles.deactivated == [USER_ID]  # 공개 프로필 비활성화
    assert tokens.popped == ["tok"]  # 리프레시 토큰 폐기
    # 손에 남은 액세스 토큰은 TTL 동안 폐기 목록으로 막는다
    assert revocations.revoked == [(USER_ID, 1800)]


async def test_진행_중_주문이_있으면_탈퇴할_수_없다():
    interactor, users, _, _, _, _ = _interactor(active=True)
    with pytest.raises(ActiveOrderExistsError):
        await interactor.delete(DeleteAccountCommand(user_id=USER_ID, refresh_token=None))
    assert users.deleted == []


async def test_잔액이_남아_있으면_탈퇴할_수_없다():
    interactor, users, _, _, _, _ = _interactor(balance=50000)
    with pytest.raises(RemainingBalanceError):
        await interactor.delete(DeleteAccountCommand(user_id=USER_ID, refresh_token=None))
    assert users.deleted == []


async def test_없는_계정이면_UserNotFoundError():
    interactor, _, _, _, _, _ = _interactor(user=None)
    with pytest.raises(UserNotFoundError):
        await interactor.delete(DeleteAccountCommand(user_id=USER_ID, refresh_token=None))


async def test_이미_탈퇴한_계정은_다시_탈퇴할_수_없다():
    from dataclasses import replace
    from datetime import datetime, timezone

    deleted_user = replace(_USER, deleted_at=datetime(2026, 8, 1, tzinfo=timezone.utc))
    interactor, _, _, _, _, _ = _interactor(user=deleted_user)
    with pytest.raises(UserNotFoundError):
        await interactor.delete(DeleteAccountCommand(user_id=USER_ID, refresh_token=None))
