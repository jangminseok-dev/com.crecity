from __future__ import annotations

from admin.app.dtos.withdrawal_settlement_dto import SettlementDecisionCommand
from admin.app.exceptions import SettlementTargetNotFoundError
from admin.app.ports.input.withdrawal_settlement_use_case import WithdrawalSettlementUseCase
from admin.app.ports.output.settlement_record_port import SettlementRecordPort
from hub.app.dtos.withdrawal_settlement_dto import WithdrawalSummary
from hub.app.ports.output.withdrawal_settlement_port import WithdrawalSettlementPort


class WithdrawalSettlementInteractor(WithdrawalSettlementUseCase):

    def __init__(self, withdrawals: WithdrawalSettlementPort, record: SettlementRecordPort) -> None:
        self._withdrawals = withdrawals
        self._record = record

    async def list_pending(self) -> list[WithdrawalSummary]:
        return await self._withdrawals.list_pending()

    async def settle(self, command: SettlementDecisionCommand) -> WithdrawalSummary:
        if command.completed:
            result = await self._withdrawals.complete(command.withdrawal_id)
        else:
            result = await self._withdrawals.fail(command.withdrawal_id)
        if result is None:
            raise SettlementTargetNotFoundError(
                f"처리 대상 인출을 찾을 수 없습니다: {command.withdrawal_id}"
            )
        decision = "지급 완료" if command.completed else "이체 실패(잔액 복원)"
        await self._record.record(
            subject="withdrawal_settlement",
            note=(
                f"인출 {result.id}(user={result.creator_user_id}, 지급액 {result.payout_krw}원) {decision} — "
                f"처리자 {command.operator_email}(user_id={command.operator_id})"
            ),
        )
        return result
