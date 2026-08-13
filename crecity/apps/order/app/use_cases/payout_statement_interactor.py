from __future__ import annotations

from order.app.dtos.payout_statement_dto import StatementQuery, StatementResult
from order.app.ports.input.payout_statement_use_case import PayoutStatementUseCase
from order.app.ports.output.withdrawal_repository import WithdrawalRepository
from order.domain.value_objects.annual_payout import AnnualPayout


class PayoutStatementInteractor(PayoutStatementUseCase):

    def __init__(self, withdrawals: WithdrawalRepository) -> None:
        self._withdrawals = withdrawals

    async def statement(self, query: StatementQuery) -> StatementResult:
        paid = await self._withdrawals.list_paid_in_year(query.year, query.user_id)
        summary = AnnualPayout.of(query.user_id, paid)
        return StatementResult.of(query.year, summary, paid)
