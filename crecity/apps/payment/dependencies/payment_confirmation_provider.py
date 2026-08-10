from __future__ import annotations

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from core.config import TOSS_SECRET_KEY
from core.database import get_db
from hub.dependencies.order_placement_provider import get_order_placement_port
from payment.adapter.outbound.gateways.toss_payments_gateway import TossPaymentsGateway
from payment.adapter.outbound.pg.payment_intent_pg_repository import PaymentIntentPgRepository
from payment.app.ports.input.payment_confirmation_use_case import PaymentConfirmationUseCase
from payment.app.use_cases.payment_confirmation_interactor import PaymentConfirmationInteractor


def get_payment_confirmation_use_case(
    db: AsyncSession = Depends(get_db),
) -> PaymentConfirmationUseCase:
    return PaymentConfirmationInteractor(
        intents=PaymentIntentPgRepository(session=db),
        gateway=TossPaymentsGateway(secret_key=TOSS_SECRET_KEY),
        orders=get_order_placement_port(),
    )
