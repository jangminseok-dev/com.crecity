from __future__ import annotations

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from notification.adapter.outbound.pg.notification_pg_repository import (
    NotificationPgRepository,
)
from notification.app.ports.input.notification_listing_use_case import (
    NotificationListingUseCase,
)
from notification.app.use_cases.notification_listing_interactor import (
    NotificationListingInteractor,
)


def get_notification_listing_use_case(
    db: AsyncSession = Depends(get_db),
) -> NotificationListingUseCase:
    return NotificationListingInteractor(notifications=NotificationPgRepository(session=db))
