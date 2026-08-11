from __future__ import annotations

import uuid

from hub.app.ports.output.campaign_application_port import CampaignApplicationPort
from hub.app.ports.output.order_adjustment_port import OrderAdjustmentPort
from hub.app.ports.output.credit_balance_port import CreditBalancePort
from hub.app.ports.output.custom_offer_port import CustomOfferPort
from hub.app.ports.output.package_summary_port import PackageSummaryPort
from payment.app.dtos.checkout_preparation_dto import (
    AdjustmentCheckoutCommand,
    ApplicationCheckoutCommand,
    CartCheckoutCommand,
    CheckoutCommand,
    CheckoutResult,
    OfferCheckoutCommand,
)
from payment.app.exceptions import NotBrandAccountError, PackageNotOrderableError
from payment.app.ports.input.checkout_preparation_use_case import CheckoutPreparationUseCase
from payment.app.ports.output.payment_intent_repository import PaymentIntentRepository


class CheckoutPreparationInteractor(CheckoutPreparationUseCase):

    def __init__(
        self,
        intents: PaymentIntentRepository,
        packages: PackageSummaryPort,
        credits: CreditBalancePort,
        brand_fee_percent: int,
        client_key: str,
        offers: CustomOfferPort | None = None,  # 커스텀 오퍼 결제에만 필요
        applications: CampaignApplicationPort | None = None,  # 지원 수락 결제에만 필요
        adjustments: OrderAdjustmentPort | None = None,  # 금액 변경 추가 결제에만 필요
    ) -> None:
        self._intents = intents
        self._packages = packages
        self._credits = credits
        self._brand_fee_percent = brand_fee_percent
        self._client_key = client_key
        self._offers = offers
        self._applications = applications
        self._adjustments = adjustments

    async def _credit_applied_krw(self, use_credit: bool, user_id: int, amount_krw: int) -> int:
        """크레딧 적용액 = min(잔액, 총액) — 조회 시점 스냅샷이며 실차감은 주문 생성이 재검증한다."""
        if not use_credit:
            return 0
        balance = await self._credits.get_balance_krw(user_id)
        return min(max(balance, 0), amount_krw)

    async def prepare(self, command: CheckoutCommand) -> CheckoutResult:
        if command.account_type != "BRAND":
            raise NotBrandAccountError("브랜드 계정만 결제할 수 있습니다.")
        summary = await self._packages.get_package_summary(command.package_id)
        if summary is None:
            raise PackageNotOrderableError(f"주문할 수 없는 패키지입니다: {command.package_id}")

        # 결제 총액 = 가격 + 브랜드 수수료 — order 도메인과 같은 정수 내림 공식(요율은 core 설정 공유)
        amount_krw = summary.price_krw + summary.price_krw * self._brand_fee_percent // 100
        credit_applied = await self._credit_applied_krw(
            command.use_credit, command.brand_user_id, amount_krw
        )
        intent = await self._intents.create(
            pg_order_id=f"crecity-{uuid.uuid4().hex}",
            package_id=command.package_id,
            brand_user_id=command.brand_user_id,
            requirements=command.requirements,
            amount_krw=amount_krw,
            credit_applied_krw=credit_applied,
        )
        return CheckoutResult(
            pg_order_id=intent.pg_order_id,
            amount_krw=intent.amount_krw,
            credit_applied_krw=intent.credit_applied_krw,
            pg_amount_krw=intent.pg_amount_krw(),
            order_name=summary.title,
            client_key=self._client_key,
        )

    async def prepare_offer(self, command: OfferCheckoutCommand) -> CheckoutResult:
        if command.account_type != "BRAND":
            raise NotBrandAccountError("브랜드 계정만 결제할 수 있습니다.")
        if self._offers is None:
            raise RuntimeError("CustomOfferPort 미주입 — 커스텀 오퍼 결제를 준비할 수 없습니다.")
        offer = await self._offers.get_payable_offer(command.offer_id)
        if offer is None:
            raise PackageNotOrderableError(f"결제할 수 없는 오퍼입니다: {command.offer_id}")
        if offer.brand_user_id != command.brand_user_id:
            raise NotBrandAccountError("이 오퍼를 받은 브랜드만 결제할 수 있습니다.")

        amount_krw = offer.price_krw + offer.price_krw * self._brand_fee_percent // 100
        credit_applied = await self._credit_applied_krw(
            command.use_credit, command.brand_user_id, amount_krw
        )
        intent = await self._intents.create(
            pg_order_id=f"crecity-{uuid.uuid4().hex}",
            package_id=None,
            brand_user_id=command.brand_user_id,
            requirements=command.requirements,
            amount_krw=amount_krw,
            offer_id=offer.offer_id,
            credit_applied_krw=credit_applied,
        )
        return CheckoutResult(
            pg_order_id=intent.pg_order_id,
            amount_krw=intent.amount_krw,
            credit_applied_krw=intent.credit_applied_krw,
            pg_amount_krw=intent.pg_amount_krw(),
            order_name=offer.title,
            client_key=self._client_key,
        )

    async def prepare_cart(self, command: CartCheckoutCommand) -> CheckoutResult:
        if command.account_type != "BRAND":
            raise NotBrandAccountError("브랜드 계정만 결제할 수 있습니다.")
        package_ids = tuple(dict.fromkeys(command.package_ids))  # 중복 제거(순서 유지)
        if not package_ids:
            raise PackageNotOrderableError("장바구니가 비어 있습니다.")

        # 총액 = 패키지별 (가격 + 브랜드 수수료) 합 — 주문별 스냅샷 공식과 일치해야 한다
        amount_krw = 0
        titles = []
        for package_id in package_ids:
            summary = await self._packages.get_package_summary(package_id)
            if summary is None:
                raise PackageNotOrderableError(f"주문할 수 없는 패키지입니다: {package_id}")
            amount_krw += summary.price_krw + summary.price_krw * self._brand_fee_percent // 100
            titles.append(summary.title)
        order_name = titles[0] if len(titles) == 1 else f"{titles[0]} 외 {len(titles) - 1}건"

        credit_applied = await self._credit_applied_krw(
            command.use_credit, command.brand_user_id, amount_krw
        )
        intent = await self._intents.create(
            pg_order_id=f"crecity-{uuid.uuid4().hex}",
            package_id=None,
            brand_user_id=command.brand_user_id,
            requirements=command.requirements,
            amount_krw=amount_krw,
            credit_applied_krw=credit_applied,
            cart_package_ids=list(package_ids),
        )
        return CheckoutResult(
            pg_order_id=intent.pg_order_id,
            amount_krw=intent.amount_krw,
            credit_applied_krw=intent.credit_applied_krw,
            pg_amount_krw=intent.pg_amount_krw(),
            order_name=order_name,
            client_key=self._client_key,
        )

    async def prepare_adjustment(self, command: AdjustmentCheckoutCommand) -> CheckoutResult:
        if command.account_type != "BRAND":
            raise NotBrandAccountError("브랜드 계정만 결제할 수 있습니다.")
        if self._adjustments is None:
            raise RuntimeError("OrderAdjustmentPort 미주입 — 추가 결제를 준비할 수 없습니다.")
        adjustment = await self._adjustments.get_payable_adjustment(command.adjustment_id)
        if adjustment is None:
            raise PackageNotOrderableError(f"결제할 수 없는 요청입니다: {command.adjustment_id}")
        if adjustment.brand_user_id != command.brand_user_id:
            raise NotBrandAccountError("주문한 브랜드만 추가 결제를 할 수 있습니다.")

        # 추가분에도 주문과 같은 수수료 공식을 적용한다
        amount_krw = (
            adjustment.extra_amount_krw
            + adjustment.extra_amount_krw * self._brand_fee_percent // 100
        )
        credit_applied = await self._credit_applied_krw(
            command.use_credit, command.brand_user_id, amount_krw
        )
        intent = await self._intents.create(
            pg_order_id=f"crecity-{uuid.uuid4().hex}",
            package_id=None,
            brand_user_id=command.brand_user_id,
            requirements="",  # 추가 결제는 새 주문을 만들지 않는다
            amount_krw=amount_krw,
            adjustment_id=adjustment.adjustment_id,
            credit_applied_krw=credit_applied,
        )
        return CheckoutResult(
            pg_order_id=intent.pg_order_id,
            amount_krw=intent.amount_krw,
            credit_applied_krw=intent.credit_applied_krw,
            pg_amount_krw=intent.pg_amount_krw(),
            order_name=f"{adjustment.order_title} — 추가 결제",
            client_key=self._client_key,
        )

    async def prepare_application(self, command: ApplicationCheckoutCommand) -> CheckoutResult:
        if command.account_type != "BRAND":
            raise NotBrandAccountError("브랜드 계정만 결제할 수 있습니다.")
        if self._applications is None:
            raise RuntimeError("CampaignApplicationPort 미주입 — 지원 수락 결제를 준비할 수 없습니다.")
        application = await self._applications.get_payable_application(command.application_id)
        if application is None:
            raise PackageNotOrderableError(f"수락할 수 없는 지원입니다: {command.application_id}")
        if application.brand_user_id != command.brand_user_id:
            raise NotBrandAccountError("공고를 올린 브랜드만 수락할 수 있습니다.")

        # 결제 총액 = 지원 견적 + 브랜드 수수료 — 패키지·오퍼 결제와 동일 공식
        amount_krw = (
            application.price_krw + application.price_krw * self._brand_fee_percent // 100
        )
        credit_applied = await self._credit_applied_krw(
            command.use_credit, command.brand_user_id, amount_krw
        )
        intent = await self._intents.create(
            pg_order_id=f"crecity-{uuid.uuid4().hex}",
            package_id=None,
            brand_user_id=command.brand_user_id,
            requirements=command.requirements,
            amount_krw=amount_krw,
            application_id=application.application_id,
            credit_applied_krw=credit_applied,
        )
        return CheckoutResult(
            pg_order_id=intent.pg_order_id,
            amount_krw=intent.amount_krw,
            credit_applied_krw=intent.credit_applied_krw,
            pg_amount_krw=intent.pg_amount_krw(),
            order_name=application.title,
            client_key=self._client_key,
        )
