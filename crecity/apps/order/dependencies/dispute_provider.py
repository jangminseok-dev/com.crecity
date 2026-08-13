from __future__ import annotations

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from order.adapter.outbound.pg.dispute_pg_repository import DisputePgRepository
from order.adapter.outbound.pg.order_pg_repository import OrderPgRepository
from order.app.ports.input.dispute_use_case import DisputeUseCase
from order.app.use_cases.dispute_interactor import DisputeInteractor


def get_dispute_use_case(db: AsyncSession = Depends(get_db)) -> DisputeUseCase:
    return DisputeInteractor(
        orders=OrderPgRepository(session=db),
        disputes=DisputePgRepository(session=db),
    )
