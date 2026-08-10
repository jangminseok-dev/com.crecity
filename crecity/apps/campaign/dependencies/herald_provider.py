from __future__ import annotations

from campaign.adapter.outbound.log_herald_record_adapter import LogHeraldRecordAdapter
from campaign.app.ports.input.herald_use_case import HeraldUseCase
from campaign.app.use_cases.herald_interactor import HeraldInteractor


def get_herald_use_case() -> HeraldUseCase:
    return HeraldInteractor(record=LogHeraldRecordAdapter())
