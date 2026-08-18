from __future__ import annotations

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from core.config import TRUST_MIN_COMPLETED_ORDERS, TRUST_MIN_VERIFIED_CHANNELS
from core.database import get_db
from creator.adapter.outbound.pg.analytics_pg_repository import AnalyticsPgRepository
from creator.adapter.outbound.pg.creator_profile_pg_repository import CreatorProfilePgRepository
from creator.app.ports.input.profile_lookup_use_case import ProfileLookupUseCase
from creator.app.use_cases.profile_lookup_interactor import ProfileLookupInteractor
from hub.dependencies.creator_trade_stats_provider import get_creator_trade_stats_port


def get_profile_lookup_use_case(
    db: AsyncSession = Depends(get_db),
) -> ProfileLookupUseCase:
    return ProfileLookupInteractor(
        repository=CreatorProfilePgRepository(session=db),
        analytics=AnalyticsPgRepository(session=db),
        trade_stats=get_creator_trade_stats_port(),
        trust_min_verified_channels=TRUST_MIN_VERIFIED_CHANNELS,
        trust_min_completed_orders=TRUST_MIN_COMPLETED_ORDERS,
    )
