from __future__ import annotations

from order.adapter.outbound.log_bookkeeper_record_adapter import LogBookkeeperRecordAdapter
from order.app.ports.input.bookkeeper_use_case import BookkeeperUseCase
from order.app.use_cases.bookkeeper_interactor import BookkeeperInteractor


def get_bookkeeper_use_case() -> BookkeeperUseCase:
    return BookkeeperInteractor(record=LogBookkeeperRecordAdapter())
