from __future__ import annotations

from creator.adapter.outbound.log_profile_record_adapter import LogProfileRecordAdapter
from creator.app.ports.input.profile_use_case import ProfileUseCase
from creator.app.use_cases.profile_interactor import ProfileInteractor


def get_profile_use_case() -> ProfileUseCase:
    return ProfileInteractor(record=LogProfileRecordAdapter())
