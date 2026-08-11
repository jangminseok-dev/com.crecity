from __future__ import annotations

from admin.adapter.outbound.log_settlement_record_adapter import LogSettlementRecordAdapter
from admin.app.ports.input.withdrawal_settlement_use_case import WithdrawalSettlementUseCase
from admin.app.use_cases.withdrawal_settlement_interactor import WithdrawalSettlementInteractor
from hub.dependencies.withdrawal_settlement_provider import get_withdrawal_settlement_port


def get_withdrawal_settlement_use_case() -> WithdrawalSettlementUseCase:
    return WithdrawalSettlementInteractor(
        withdrawals=get_withdrawal_settlement_port(),
        record=LogSettlementRecordAdapter(),
    )
