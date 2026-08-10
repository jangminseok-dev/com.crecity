from __future__ import annotations

from payment.adapter.outbound.log_paymaster_record_adapter import LogPaymasterRecordAdapter
from payment.app.ports.input.paymaster_use_case import PaymasterUseCase
from payment.app.use_cases.paymaster_interactor import PaymasterInteractor


def get_paymaster_use_case() -> PaymasterUseCase:
    return PaymasterInteractor(record=LogPaymasterRecordAdapter())
