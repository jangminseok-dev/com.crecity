from __future__ import annotations

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from order.adapter.outbound.pg.order_pg_repository import OrderPgRepository
from order.app.ports.input.order_lookup_use_case import OrderLookupUseCase
from order.app.use_cases.order_lookup_interactor import OrderLookupInteractor


def get_order_lookup_use_case(
    db: AsyncSession = Depends(get_db),
) -> OrderLookupUseCase:
    return OrderLookupInteractor(orders=OrderPgRepository(session=db))
