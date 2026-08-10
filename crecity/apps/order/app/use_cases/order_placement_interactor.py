from __future__ import annotations

from datetime import datetime, timedelta, timezone

from hub.app.ports.output.package_summary_port import PackageSummaryPort
from order.app.dtos.order_placement_dto import OrderPlacementCommand
from order.app.dtos.order_result_dto import OrderResult
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
    ) -> None:
        self._orders = orders
        self._packages = packages
        self._brand_fee_percent = brand_fee_percent
        self._creator_fee_percent = creator_fee_percent
        self._accept_deadline = accept_deadline

    async def place(self, command: OrderPlacementCommand) -> OrderResult:
        if command.account_type != "BRAND":
            raise NotBrandAccountError("브랜드 계정만 주문할 수 있습니다.")
        summary = await self._packages.get_package_summary(command.package_id)
        if summary is None:
            raise PackageNotOrderableError(f"주문할 수 없는 패키지입니다: {command.package_id}")

        now = datetime.now(timezone.utc)
        draft = Order(
            id=0,  # 저장 시 발급
            package_id=summary.package_id,
            package_title=summary.title,
            brand_user_id=command.brand_user_id,
            creator_user_id=summary.creator_user_id,
            amount_krw=summary.price_krw,
            brand_fee_percent=self._brand_fee_percent,
            creator_fee_percent=self._creator_fee_percent,
            requirements=command.requirements,
            status=OrderStatus.PENDING_ACCEPT,
            deadline_at=now + self._accept_deadline,
        )
        deposit = LedgerEntryDraft(
            entry_type=LedgerEntryType.ESCROW_DEPOSIT,
            user_id=command.brand_user_id,
            amount_krw=draft.brand_total_krw(),
        )
        order = await self._orders.create(draft, [deposit])
        return OrderResult.from_order(order)
