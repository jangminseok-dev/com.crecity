from __future__ import annotations

from chat.adapter.outbound.log_courier_record_adapter import LogCourierRecordAdapter
from chat.app.ports.input.courier_use_case import CourierUseCase
from chat.app.use_cases.courier_interactor import CourierInteractor


def get_courier_use_case() -> CourierUseCase:
    return CourierInteractor(record=LogCourierRecordAdapter())
