from __future__ import annotations

from review.adapter.outbound.log_appraiser_record_adapter import LogAppraiserRecordAdapter
from review.app.ports.input.appraiser_use_case import AppraiserUseCase
from review.app.use_cases.appraiser_interactor import AppraiserInteractor


def get_appraiser_use_case() -> AppraiserUseCase:
    return AppraiserInteractor(record=LogAppraiserRecordAdapter())
