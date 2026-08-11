from __future__ import annotations

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from core.config import ORDER_BRAND_FEE_PERCENT, TOSS_CLIENT_KEY
from core.database import get_db
from hub.dependencies.credit_balance_provider import get_credit_balance_port
from hub.dependencies.custom_offer_provider import get_custom_offer_port
from hub.dependencies.package_summary_provider import get_package_summary_port
from payment.adapter.outbound.pg.payment_intent_pg_repository import PaymentIntentPgRepository
from payment.app.ports.input.checkout_preparation_use_case import CheckoutPreparationUseCase
from payment.app.use_cases.checkout_preparation_interactor import CheckoutPreparationInteractor


def get_checkout_preparation_use_case(
    db: AsyncSession = Depends(get_db),
) -> CheckoutPreparationUseCase:
    return CheckoutPreparationInteractor(
        intents=PaymentIntentPgRepository(session=db),
        packages=get_package_summary_port(),
        credits=get_credit_balance_port(),
        brand_fee_percent=ORDER_BRAND_FEE_PERCENT,
        client_key=TOSS_CLIENT_KEY,
        offers=get_custom_offer_port(),
    )
