from __future__ import annotations

import uuid

from hub.app.ports.output.custom_offer_port import CustomOfferPort
from hub.app.ports.output.package_summary_port import PackageSummaryPort
from payment.app.dtos.checkout_preparation_dto import (
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
        brand_fee_percent: int,
        client_key: str,
        offers: CustomOfferPort | None = None,  # 커스텀 오퍼 결제에만 필요
    ) -> None:
        self._intents = intents
        self._packages = packages
        self._brand_fee_percent = brand_fee_percent
        self._client_key = client_key
        self._offers = offers

    async def prepare(self, command: CheckoutCommand) -> CheckoutResult:
        if command.account_type != "BRAND":
            raise NotBrandAccountError("브랜드 계정만 결제할 수 있습니다.")
        summary = await self._packages.get_package_summary(command.package_id)
        if summary is None:
            raise PackageNotOrderableError(f"주문할 수 없는 패키지입니다: {command.package_id}")

        # 결제 총액 = 가격 + 브랜드 수수료 — order 도메인과 같은 정수 내림 공식(요율은 core 설정 공유)
        amount_krw = summary.price_krw + summary.price_krw * self._brand_fee_percent // 100
        intent = await self._intents.create(
            pg_order_id=f"crecity-{uuid.uuid4().hex}",
            package_id=command.package_id,
            brand_user_id=command.brand_user_id,
            requirements=command.requirements,
            amount_krw=amount_krw,
        )
        return CheckoutResult(
            pg_order_id=intent.pg_order_id,
            amount_krw=intent.amount_krw,
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
        intent = await self._intents.create(
            pg_order_id=f"crecity-{uuid.uuid4().hex}",
            package_id=None,
            brand_user_id=command.brand_user_id,
            requirements=command.requirements,
            amount_krw=amount_krw,
            offer_id=offer.offer_id,
        )
        return CheckoutResult(
            pg_order_id=intent.pg_order_id,
            amount_krw=intent.amount_krw,
            order_name=offer.title,
            client_key=self._client_key,
        )
