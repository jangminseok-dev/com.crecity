from __future__ import annotations

from datetime import timedelta

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from core.config import (
    ORDER_BRAND_FEE_PERCENT,
    ORDER_CREATOR_FEE_PERCENT,
    ORDER_RESPONSE_DEADLINE_HOURS,
)
from core.database import get_db
from hub.dependencies.package_summary_provider import get_package_summary_port
from order.adapter.outbound.pg.order_pg_repository import OrderPgRepository
from order.app.ports.input.order_placement_use_case import OrderPlacementUseCase
from order.app.use_cases.order_placement_interactor import OrderPlacementInteractor


def get_order_placement_use_case(
    db: AsyncSession = Depends(get_db),
) -> OrderPlacementUseCase:
    return OrderPlacementInteractor(
        orders=OrderPgRepository(session=db),
        packages=get_package_summary_port(),
        brand_fee_percent=ORDER_BRAND_FEE_PERCENT,
        creator_fee_percent=ORDER_CREATOR_FEE_PERCENT,
        accept_deadline=timedelta(hours=ORDER_RESPONSE_DEADLINE_HOURS),
    )
