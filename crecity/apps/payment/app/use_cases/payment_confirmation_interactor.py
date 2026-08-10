from __future__ import annotations

import logging

from hub.app.ports.output.custom_offer_port import CustomOfferPort
from hub.app.ports.output.order_placement_port import OrderPlacementPort
from payment.app.dtos.payment_confirmation_dto import ConfirmCommand, ConfirmResult
from payment.app.exceptions import (
    NotPaymentOwnerError,
    PaymentAlreadyProcessedError,
    PaymentAmountMismatchError,
    PaymentConfirmError,
    PaymentIntentNotFoundError,
)
from payment.app.ports.input.payment_confirmation_use_case import PaymentConfirmationUseCase
from payment.app.ports.output.payment_gateway import PaymentGateway
from payment.app.ports.output.payment_intent_repository import PaymentIntentRepository

logger = logging.getLogger(__name__)


class PaymentConfirmationInteractor(PaymentConfirmationUseCase):

    def __init__(
        self,
        intents: PaymentIntentRepository,
        gateway: PaymentGateway,
        orders: OrderPlacementPort,
        offers: CustomOfferPort | None = None,  # 커스텀 오퍼 결제에만 필요
    ) -> None:
        self._intents = intents
        self._gateway = gateway
        self._orders = orders
        self._offers = offers

    async def confirm(self, command: ConfirmCommand) -> ConfirmResult:
        intent = await self._intents.find_by_pg_order_id(command.pg_order_id)
        if intent is None:
            raise PaymentIntentNotFoundError(f"결제 정보를 찾을 수 없습니다: {command.pg_order_id}")
        if not intent.is_owned_by(command.requester_user_id):
            raise NotPaymentOwnerError("본인 결제만 승인할 수 있습니다.")
        if not intent.is_ready():
            raise PaymentAlreadyProcessedError("이미 처리된 결제입니다.")
        if not intent.matches_amount(command.amount_krw):
            await self._intents.mark_failed(intent.id, None, "금액 불일치(위변조 의심)")
            raise PaymentAmountMismatchError("결제 금액이 일치하지 않습니다 — 처음부터 다시 시도해 주세요.")

        # 1) PG 승인 (외부 접점 — 실패는 기록 후 통보)
        try:
            await self._gateway.confirm(command.payment_key, command.pg_order_id, intent.amount_krw)
        except PaymentConfirmError as error:
            await self._intents.mark_failed(intent.id, command.payment_key, f"승인 실패: {error}")
            raise

        # 2) 주문 생성+예치 (order 내부 원자적 — §3). 실패 시 PG 취소로 보정한다.
        if intent.offer_id is not None:
            placed = await self._orders.place_paid_custom_order(
                offer_id=intent.offer_id,
                requirements=intent.requirements,
                brand_user_id=intent.brand_user_id,
                expected_brand_total_krw=intent.amount_krw,
            )
        else:
            placed = await self._orders.place_paid_order(
                package_id=intent.package_id,
                requirements=intent.requirements,
                brand_user_id=intent.brand_user_id,
                expected_brand_total_krw=intent.amount_krw,
            )
        if placed is None:
            try:
                await self._gateway.cancel(command.payment_key, "주문 생성 실패 — 자동 환불")
                reason = "주문 생성 실패 — 결제 취소 보정 완료"
            except PaymentConfirmError:
                # 취소까지 실패 — 기록을 남겨 운영 개입으로 수렴시킨다(§3: 재시도 가능한 보정)
                logger.error("결제 취소 보정 실패: pg_order_id=%s", intent.pg_order_id)
                reason = "주문 생성 실패 — 결제 취소 보정도 실패(운영 확인 필요)"
            await self._intents.mark_failed(intent.id, command.payment_key, reason)
            raise PaymentConfirmError("주문 생성에 실패해 결제를 취소했습니다 — 다시 시도해 주세요.")

        await self._intents.mark_confirmed(intent.id, command.payment_key, placed.id)
        # 오퍼 결제 완료 표시 — 재결제 차단(표시용, 주문·원장과 별개라 결과적 정합성으로 충분)
        if intent.offer_id is not None and self._offers is not None:
            await self._offers.mark_paid(intent.offer_id, placed.id)
        return ConfirmResult(order_id=placed.id)
