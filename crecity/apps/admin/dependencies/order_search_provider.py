from __future__ import annotations

from fastapi import Depends

from admin.app.ports.input.order_search_use_case import OrderSearchUseCase
from admin.app.use_cases.order_search_interactor import OrderSearchInteractor
from hub.app.ports.output.order_search_port import OrderSearchPort
from hub.dependencies.order_search_provider import get_order_search_port


def get_order_search_use_case(
    orders: OrderSearchPort = Depends(get_order_search_port),
) -> OrderSearchUseCase:
    return OrderSearchInteractor(orders=orders)
