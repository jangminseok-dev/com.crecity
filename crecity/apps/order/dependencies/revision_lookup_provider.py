from __future__ import annotations

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from order.adapter.outbound.pg.order_pg_repository import OrderPgRepository
from order.adapter.outbound.pg.revision_request_pg_repository import (
    RevisionRequestPgRepository,
)
from order.app.ports.input.revision_lookup_use_case import RevisionLookupUseCase
from order.app.use_cases.revision_lookup_interactor import RevisionLookupInteractor


def get_revision_lookup_use_case(
    db: AsyncSession = Depends(get_db),
) -> RevisionLookupUseCase:
    return RevisionLookupInteractor(
        orders=OrderPgRepository(session=db),
        revisions=RevisionRequestPgRepository(session=db),
    )
