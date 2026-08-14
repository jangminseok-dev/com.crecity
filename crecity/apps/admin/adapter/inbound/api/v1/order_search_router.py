from fastapi import APIRouter, Depends, Query

from admin.adapter.inbound.api.schemas.order_search_schema import (
    AdminOrderSearchResponseSchema,
)
from admin.app.dtos.order_search_dto import OrderSearchQuery
from admin.app.ports.input.order_search_use_case import OrderSearchUseCase
from admin.dependencies.order_search_provider import get_order_search_use_case
from hub.dependencies.current_user_provider import require_permission

order_search_router = APIRouter(prefix="/admin", tags=["admin"])

# 남의 주문 내역을 들여다보는 기능이라 전용 권한을 둔다
_searcher = require_permission("order.search")


@order_search_router.get("/orders", response_model=AdminOrderSearchResponseSchema)
async def search_orders(
    order_id: int | None = Query(None, ge=1, description="주문 번호 정확 일치"),
    # 상태는 order 소유 어휘 — admin이 enum을 import하면 스포크 독립이 깨지므로 문자열로 받는다
    # (PENDING_ACCEPT·IN_PROGRESS·IN_REVIEW·COMPLETED·REFUNDED·CANCELLED)
    status: str | None = Query(None, max_length=20, description="주문 상태"),
    user_id: int | None = Query(None, ge=1, description="브랜드·크리에이터 어느 쪽이든 참여한 주문"),
    limit: int = Query(20, ge=1, le=50),
    offset: int = Query(0, ge=0),
    _actor=Depends(_searcher),
    use_case: OrderSearchUseCase = Depends(get_order_search_use_case),
) -> AdminOrderSearchResponseSchema:
    result = await use_case.search(
        OrderSearchQuery(
            order_id=order_id,
            status=status,
            user_id=user_id,
            limit=limit,
            offset=offset,
        )
    )
    return AdminOrderSearchResponseSchema.from_result(result)
