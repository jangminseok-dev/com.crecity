from __future__ import annotations

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from order.adapter.outbound.local_deliverable_file_storage import LocalDeliverableFileStorage
from order.adapter.outbound.pg.deliverable_pg_repository import DeliverablePgRepository
from order.adapter.outbound.pg.order_pg_repository import OrderPgRepository
from order.app.ports.input.deliverable_submission_use_case import DeliverableSubmissionUseCase
from order.app.use_cases.deliverable_submission_interactor import (
    DeliverableSubmissionInteractor,
)


def get_deliverable_submission_use_case(
    db: AsyncSession = Depends(get_db),
) -> DeliverableSubmissionUseCase:
    return DeliverableSubmissionInteractor(
        orders=OrderPgRepository(session=db),
        deliverables=DeliverablePgRepository(session=db),
        storage=LocalDeliverableFileStorage(),
    )
