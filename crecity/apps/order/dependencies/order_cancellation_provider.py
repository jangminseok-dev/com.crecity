from __future__ import annotations

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from order.adapter.outbound.pg.order_pg_repository import OrderPgRepository
from order.app.ports.input.order_cancellation_use_case import OrderCancellationUseCase
from order.app.use_cases.order_cancellation_interactor import OrderCancellationInteractor


def get_order_cancellation_use_case(
    db: AsyncSession = Depends(get_db),
) -> OrderCancellationUseCase:
    return OrderCancellationInteractor(orders=OrderPgRepository(session=db))
