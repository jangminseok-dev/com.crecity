from __future__ import annotations

from auth.app.dtos.account_deletion_dto import DeleteAccountCommand
from auth.app.exceptions import (
    ActiveOrderExistsError,
    RemainingBalanceError,
    UserNotFoundError,
)
from auth.app.ports.input.account_deletion_use_case import AccountDeletionUseCase
from auth.app.ports.output.refresh_token_store import RefreshTokenStore
from auth.app.ports.output.social_identity_repository import SocialIdentityRepository
from auth.app.ports.output.user_repository import UserRepository
from hub.app.ports.output.active_order_port import ActiveOrderPort
from hub.app.ports.output.credit_balance_port import CreditBalancePort
from hub.app.ports.output.profile_deactivation_port import ProfileDeactivationPort

# 탈퇴 계정 이메일 — 재가입을 막지 않으면서 unique 제약을 지키는 익명값
_ANONYMIZED_EMAIL_DOMAIN = "deleted.crecity.invalid"


class AccountDeletionInteractor(AccountDeletionUseCase):

    def __init__(
        self,
        users: UserRepository,
        identities: SocialIdentityRepository,
        refresh_tokens: RefreshTokenStore,
        active_orders: ActiveOrderPort,
        balances: CreditBalancePort,
        profiles: ProfileDeactivationPort,
    ) -> None:
        self._users = users
        self._identities = identities
        self._refresh_tokens = refresh_tokens
        self._active_orders = active_orders
        self._balances = balances
        self._profiles = profiles

    async def delete(self, command: DeleteAccountCommand) -> None:
        user = await self._users.find_by_id(command.user_id)
        if user is None or user.is_deleted():
            raise UserNotFoundError("계정을 찾을 수 없습니다.")
        if await self._active_orders.has_active_orders(user.id):
            raise ActiveOrderExistsError(
                "진행 중인 주문이 있어 탈퇴할 수 없습니다 — 주문을 마친 뒤 다시 시도해 주세요."
            )
        if await self._balances.get_balance_krw(user.id) > 0:
            raise RemainingBalanceError(
                "잔액이 남아 있어 탈퇴할 수 없습니다 — 인출하거나 사용한 뒤 다시 시도해 주세요."
            )

        # 공개 노출부터 끊고(프로필) 로그인 수단을 제거한 뒤 계정을 익명화한다
        await self._profiles.deactivate_profile(user.id)
        await self._identities.delete_by_user_id(user.id)
        await self._users.soft_delete(
            user.id, f"deleted-{user.id}@{_ANONYMIZED_EMAIL_DOMAIN}"
        )
        if command.refresh_token:
            await self._refresh_tokens.pop(command.refresh_token)
