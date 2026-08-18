from __future__ import annotations

from sqlalchemy import select

from core.database import session_scope
from hub.app.dtos.completed_order_price_dto import PackageOrderAmount
from hub.app.ports.output.completed_order_price_port import CompletedOrderPricePort
from order.adapter.outbound.orm.order_orm import OrderOrm
from order.domain.entities.order_entity import OrderStatus

# 시세 집계 상한 — 최신 완료 주문부터 이만큼만 본다(대량화되면 주기 집계 테이블로 전환).
_AMOUNTS_CAP = 10_000


class OrderCompletedPriceGateway(CompletedOrderPricePort):
    """허브 CompletedOrderPricePort 계약의 order 구현 — main.py가 조립한다.

    호출자(creator 시세 집계) 트랜잭션과 무관한 읽기 전용 조회라 자체 세션을 연다.
    """

    async def list_completed_package_amounts(self) -> list[PackageOrderAmount]:
        async with session_scope() as session:
            result = await session.execute(
                select(OrderOrm.package_id, OrderOrm.amount_krw)
                .where(
                    OrderOrm.status == OrderStatus.COMPLETED.value,
                    OrderOrm.package_id.is_not(None),  # 커스텀 오퍼는 분류 불가라 제외
                )
                .order_by(OrderOrm.id.desc())
                .limit(_AMOUNTS_CAP)
            )
            return [
                PackageOrderAmount(package_id=package_id, amount_krw=int(amount))
                for package_id, amount in result
            ]
