from __future__ import annotations

import logging
from datetime import timedelta

from core.config import (
    ORDER_BRAND_FEE_PERCENT,
    ORDER_CREATOR_FEE_PERCENT,
    ORDER_RESPONSE_DEADLINE_HOURS,
)
from core.database import session_scope
from hub.app.dtos.placed_order_dto import PlacedOrder
from hub.app.ports.output.order_placement_port import OrderPlacementPort
from hub.dependencies.custom_offer_provider import get_custom_offer_port
from hub.dependencies.package_summary_provider import get_package_summary_port
from order.adapter.outbound.pg.order_pg_repository import OrderPgRepository
from order.app.dtos.order_placement_dto import (
    CustomOrderPlacementCommand,
    OrderPlacementCommand,
)
from order.app.exceptions import NotBrandAccountError, PackageNotOrderableError
from order.app.use_cases.order_placement_interactor import OrderPlacementInteractor

logger = logging.getLogger(__name__)


class PaidOrderPlacementGateway(OrderPlacementPort):
    """허브 OrderPlacementPort 계약의 order 구현 — main.py가 조립한다.

    결제 승인 뒤 호출되므로 실패는 예외 대신 None으로 알린다(payment가 PG 취소로 보정).
    """

    async def place_paid_order(
        self,
        package_id: int,
        requirements: str,
        brand_user_id: int,
        expected_brand_total_krw: int,
    ) -> PlacedOrder | None:
        packages = get_package_summary_port()
        summary = await packages.get_package_summary(package_id)
        if summary is None:
            return None
        # 결제 시점 금액과 현재 계산이 다르면(가격 변동) 주문을 만들지 않는다
        current_total = summary.price_krw + summary.price_krw * ORDER_BRAND_FEE_PERCENT // 100
        if current_total != expected_brand_total_krw:
            logger.warning(
                "결제-주문 금액 불일치: package=%s 결제=%s 현재=%s",
                package_id, expected_brand_total_krw, current_total,
            )
            return None
        try:
            async with session_scope() as session:
                interactor = OrderPlacementInteractor(
                    orders=OrderPgRepository(session=session),
                    packages=packages,
                    brand_fee_percent=ORDER_BRAND_FEE_PERCENT,
                    creator_fee_percent=ORDER_CREATOR_FEE_PERCENT,
                    accept_deadline=timedelta(hours=ORDER_RESPONSE_DEADLINE_HOURS),
                )
                result = await interactor.place(
                    OrderPlacementCommand(
                        package_id=package_id,
                        requirements=requirements,
                        brand_user_id=brand_user_id,
                        account_type="BRAND",  # 결제 시점에 BRAND 검증 완료(payment 몫)
                    )
                )
        except (NotBrandAccountError, PackageNotOrderableError):
            return None
        return PlacedOrder(id=result.id, brand_total_krw=result.brand_total_krw)

    async def place_paid_custom_order(
        self,
        offer_id: int,
        requirements: str,
        brand_user_id: int,
        expected_brand_total_krw: int,
    ) -> PlacedOrder | None:
        offers = get_custom_offer_port()
        summary = await offers.get_payable_offer(offer_id)
        if summary is None:
            return None
        # 결제 시점 금액과 현재 계산이 다르면 주문을 만들지 않는다(패키지 주문과 동일 방어)
        current_total = summary.price_krw + summary.price_krw * ORDER_BRAND_FEE_PERCENT // 100
        if current_total != expected_brand_total_krw:
            logger.warning(
                "결제-오퍼 금액 불일치: offer=%s 결제=%s 현재=%s",
                offer_id, expected_brand_total_krw, current_total,
            )
            return None
        try:
            async with session_scope() as session:
                interactor = OrderPlacementInteractor(
                    orders=OrderPgRepository(session=session),
                    packages=get_package_summary_port(),
                    brand_fee_percent=ORDER_BRAND_FEE_PERCENT,
                    creator_fee_percent=ORDER_CREATOR_FEE_PERCENT,
                    accept_deadline=timedelta(hours=ORDER_RESPONSE_DEADLINE_HOURS),
                    offers=offers,
                )
                result = await interactor.place_custom(
                    CustomOrderPlacementCommand(
                        offer_id=offer_id,
                        requirements=requirements,
                        brand_user_id=brand_user_id,
                        account_type="BRAND",  # 결제 시점에 BRAND 검증 완료(payment 몫)
                    )
                )
        except (NotBrandAccountError, PackageNotOrderableError):
            return None
        return PlacedOrder(id=result.id, brand_total_krw=result.brand_total_krw)
