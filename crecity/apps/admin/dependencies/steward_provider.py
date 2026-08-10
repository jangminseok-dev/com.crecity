from __future__ import annotations

from admin.adapter.outbound.log_steward_record_adapter import LogStewardRecordAdapter
from admin.app.ports.input.steward_use_case import StewardUseCase
from admin.app.use_cases.steward_interactor import StewardInteractor


def get_steward_use_case() -> StewardUseCase:
    return StewardInteractor(record=LogStewardRecordAdapter())
