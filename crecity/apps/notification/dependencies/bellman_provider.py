from __future__ import annotations

from notification.adapter.outbound.log_bellman_record_adapter import LogBellmanRecordAdapter
from notification.app.ports.input.bellman_use_case import BellmanUseCase
from notification.app.use_cases.bellman_interactor import BellmanInteractor


def get_bellman_use_case() -> BellmanUseCase:
    return BellmanInteractor(record=LogBellmanRecordAdapter())
