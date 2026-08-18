from __future__ import annotations

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from core.config import (
    ANOMALY_ENGAGEMENT_FOLLOWER_FLOOR,
    ANOMALY_FOLLOWER_SURGE_MULTIPLIER,
    ANOMALY_MAX_ENGAGEMENT_PERMILLE,
)
from core.database import get_db
from creator.adapter.outbound.local_analytics_file_storage import LocalAnalyticsFileStorage
from creator.adapter.outbound.pg.analytics_pg_repository import AnalyticsPgRepository
from creator.adapter.outbound.pg.creator_profile_pg_repository import CreatorProfilePgRepository
from creator.app.ports.input.analytics_management_use_case import AnalyticsManagementUseCase
from creator.app.use_cases.analytics_management_interactor import (
    AnalyticsManagementInteractor,
)


def get_analytics_management_use_case(
    db: AsyncSession = Depends(get_db),
) -> AnalyticsManagementUseCase:
    return AnalyticsManagementInteractor(
        profiles=CreatorProfilePgRepository(session=db),
        analytics=AnalyticsPgRepository(session=db),
        storage=LocalAnalyticsFileStorage(),
        anomaly_surge_multiplier=ANOMALY_FOLLOWER_SURGE_MULTIPLIER,
        anomaly_engagement_floor=ANOMALY_ENGAGEMENT_FOLLOWER_FLOOR,
        anomaly_max_engagement_permille=ANOMALY_MAX_ENGAGEMENT_PERMILLE,
    )
