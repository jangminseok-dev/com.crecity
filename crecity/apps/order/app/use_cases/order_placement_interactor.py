from __future__ import annotations

from datetime import datetime, timedelta, timezone

from hub.app.ports.output.custom_offer_port import CustomOfferPort
from hub.app.ports.output.package_summary_port import PackageSummaryPort
from order.app.dtos.order_placement_dto import (
    CustomOrderPlacementCommand,
    OrderPlacementCommand,
)
from order.app.dtos.order_result_dto import OrderResult
from order.app.events import order_event
from order.app.exceptions import NotBrandAccountError, PackageNotOrderableError
from order.app.ports.input.order_placement_use_case import OrderPlacementUseCase
from order.app.ports.output.order_repository import OrderRepository
from order.domain.entities.ledger_entry_entity import LedgerEntryDraft, LedgerEntryType
from order.domain.entities.order_entity import Order, OrderStatus


class OrderPlacementInteractor(OrderPlacementUseCase):

    def __init__(
        self,
        orders: OrderRepository,
        packages: PackageSummaryPort,
        brand_fee_percent: int,
        creator_fee_percent: int,
        accept_deadline: timedelta,
        offers: CustomOfferPort | None = None,  # 커스텀 오퍼 주문에만 필요
    ) -> None:
        self._orders = orders
        self._packages = packages
        self._brand_fee_percent = brand_fee_percent
        self._creator_fee_percent = creator_fee_percent
        self._accept_deadline = accept_deadline
        self._offers = offers

    async def place(self, command: OrderPlacementCommand) -> OrderResult:
        if command.account_type != "BRAND":
            raise NotBrandAccountError("브랜드 계정만 주문할 수 있습니다.")
        summary = await self._packages.get_package_summary(command.package_id)
        if summary is None:
            raise PackageNotOrderableError(f"주문할 수 없는 패키지입니다: {command.package_id}")

        return await self._place(
            package_id=summary.package_id,
            title=summary.title,
            price_krw=summary.price_krw,
            creator_user_id=summary.creator_user_id,
            brand_user_id=command.brand_user_id,
            requirements=command.requirements,
        )

    async def place_custom(self, command: CustomOrderPlacementCommand) -> OrderResult:
        if command.account_type != "BRAND":
            raise NotBrandAccountError("브랜드 계정만 주문할 수 있습니다.")
        if self._offers is None:
            raise RuntimeError("CustomOfferPort 미주입 — 커스텀 오퍼 주문을 만들 수 없습니다.")
        offer = await self._offers.get_payable_offer(command.offer_id)
        if offer is None:
            raise PackageNotOrderableError(f"결제할 수 없는 오퍼입니다: {command.offer_id}")
        if offer.brand_user_id != command.brand_user_id:
            raise NotBrandAccountError("이 오퍼를 받은 브랜드만 결제할 수 있습니다.")
        return await self._place(
            package_id=None,  # 커스텀 오퍼 주문 — 패키지 없음
            title=offer.title,
            price_krw=offer.price_krw,
            creator_user_id=offer.creator_user_id,
            brand_user_id=command.brand_user_id,
            requirements=command.requirements,
        )

    async def _place(
        self,
        package_id: int | None,
        title: str,
        price_krw: int,
        creator_user_id: int,
        brand_user_id: int,
        requirements: str,
    ) -> OrderResult:
        now = datetime.now(timezone.utc)
        draft = Order(
            id=0,  # 저장 시 발급
            package_id=package_id,
            package_title=title,
            brand_user_id=brand_user_id,
            creator_user_id=creator_user_id,
            amount_krw=price_krw,
            brand_fee_percent=self._brand_fee_percent,
            creator_fee_percent=self._creator_fee_percent,
            requirements=requirements,
            status=OrderStatus.PENDING_ACCEPT,
            deadline_at=now + self._accept_deadline,
        )
        deposit = LedgerEntryDraft(
            entry_type=LedgerEntryType.ESCROW_DEPOSIT,
            user_id=brand_user_id,
            amount_krw=draft.brand_total_krw(),
        )
        # order_id는 저장 시점에 리포지토리가 payload에 채운다
        placed_event = order_event("order.placed", draft)
        order = await self._orders.create(draft, [deposit], [placed_event])
        return OrderResult.from_order(order)
