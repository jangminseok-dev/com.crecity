from __future__ import annotations

from datetime import timedelta

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from core.config import ORDER_RESPONSE_DEADLINE_HOURS
from core.database import get_db
from order.adapter.outbound.pg.order_pg_repository import OrderPgRepository
from order.app.ports.input.order_progress_use_case import OrderProgressUseCase
from order.app.use_cases.order_progress_interactor import OrderProgressInteractor


def get_order_progress_use_case(
    db: AsyncSession = Depends(get_db),
) -> OrderProgressUseCase:
    return OrderProgressInteractor(
        orders=OrderPgRepository(session=db),
        review_deadline=timedelta(hours=ORDER_RESPONSE_DEADLINE_HOURS),
    )
