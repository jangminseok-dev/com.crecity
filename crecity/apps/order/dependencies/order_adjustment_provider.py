from __future__ import annotations

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from order.adapter.outbound.pg.adjustment_pg_repository import AdjustmentPgRepository
from order.adapter.outbound.pg.order_pg_repository import OrderPgRepository
from order.app.ports.input.order_adjustment_use_case import OrderAdjustmentUseCase
from order.app.use_cases.order_adjustment_interactor import OrderAdjustmentInteractor


def get_order_adjustment_use_case(
    db: AsyncSession = Depends(get_db),
) -> OrderAdjustmentUseCase:
    return OrderAdjustmentInteractor(
        orders=OrderPgRepository(session=db),
        adjustments=AdjustmentPgRepository(session=db),
    )
