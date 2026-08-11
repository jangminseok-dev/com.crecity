from __future__ import annotations

from order.app.dtos.withdrawal_request_dto import WithdrawalRequestCommand, WithdrawalResult
from order.app.exceptions import InsufficientBalanceError, NotCreatorAccountError
from order.app.ports.input.withdrawal_request_use_case import WithdrawalRequestUseCase
from order.app.ports.output.withdrawal_repository import WithdrawalRepository
from order.domain.entities.withdrawal_entity import Withdrawal, compute_withholding_tax


class WithdrawalRequestInteractor(WithdrawalRequestUseCase):

    def __init__(self, withdrawals: WithdrawalRepository, tax_permille: int) -> None:
        self._withdrawals = withdrawals
        self._tax_permille = tax_permille

    @staticmethod
    def _to_result(withdrawal: Withdrawal) -> WithdrawalResult:
        return WithdrawalResult(
            id=withdrawal.id,
            amount_krw=withdrawal.amount_krw,
            tax_krw=withdrawal.tax_krw,
            payout_krw=withdrawal.payout_krw,
            bank_name=withdrawal.bank_name,
            account_number=withdrawal.account_number,
            account_holder=withdrawal.account_holder,
            status=withdrawal.status.value,
            created_at=withdrawal.created_at,
            settled_at=withdrawal.settled_at,
        )

    async def request(self, command: WithdrawalRequestCommand) -> WithdrawalResult:
        if command.account_type != "CREATOR":
            raise NotCreatorAccountError("크리에이터 계정만 적립금을 인출할 수 있습니다.")
        if command.amount_krw <= 0:
            raise ValueError("인출 금액은 1원 이상이어야 합니다.")
        if not command.bank_name.strip() or not command.account_number.strip() or not command.account_holder.strip():
            raise ValueError("은행명·계좌번호·예금주를 모두 입력해 주세요.")

        tax_krw = compute_withholding_tax(command.amount_krw, self._tax_permille)
        withdrawal = await self._withdrawals.create_if_balance_sufficient(
            user_id=command.user_id,
            amount_krw=command.amount_krw,
            tax_krw=tax_krw,
            payout_krw=command.amount_krw - tax_krw,
            bank_name=command.bank_name.strip(),
            account_number=command.account_number.strip(),
            account_holder=command.account_holder.strip(),
        )
        if withdrawal is None:
            raise InsufficientBalanceError("잔액이 부족합니다.")
        return self._to_result(withdrawal)

    async def list_mine(self, user_id: int) -> list[WithdrawalResult]:
        return [self._to_result(w) for w in await self._withdrawals.list_by_user(user_id)]
