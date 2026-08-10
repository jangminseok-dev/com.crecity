from fastapi import APIRouter, Depends, HTTPException

from hub.app.dtos.verified_user_dto import VerifiedUser
from hub.dependencies.current_user_provider import get_current_user
from payment.adapter.inbound.api.schemas.checkout_preparation_schema import (
    CheckoutRequestSchema,
    CheckoutResponseSchema,
    OfferCheckoutRequestSchema,
)
from payment.app.dtos.checkout_preparation_dto import CheckoutCommand, OfferCheckoutCommand
from payment.app.exceptions import NotBrandAccountError, PackageNotOrderableError
from payment.app.ports.input.checkout_preparation_use_case import CheckoutPreparationUseCase
from payment.dependencies.checkout_preparation_provider import get_checkout_preparation_use_case

checkout_preparation_router = APIRouter(prefix="/payment", tags=["payment"])


@checkout_preparation_router.post(
    "/checkouts", response_model=CheckoutResponseSchema, status_code=201
)
async def prepare_checkout(
    body: CheckoutRequestSchema,
    user: VerifiedUser = Depends(get_current_user),
    use_case: CheckoutPreparationUseCase = Depends(get_checkout_preparation_use_case),
) -> CheckoutResponseSchema:
    try:
        result = await use_case.prepare(
            CheckoutCommand(
                package_id=body.package_id,
                requirements=body.requirements,
                brand_user_id=user.id,
                account_type=user.account_type,
            )
        )
    except NotBrandAccountError as error:
        raise HTTPException(status_code=403, detail=str(error))
    except PackageNotOrderableError as error:
        raise HTTPException(status_code=404, detail=str(error))
    return CheckoutResponseSchema(
        pg_order_id=result.pg_order_id,
        amount_krw=result.amount_krw,
        order_name=result.order_name,
        client_key=result.client_key,
    )


@checkout_preparation_router.post(
    "/checkouts/offer", response_model=CheckoutResponseSchema, status_code=201
)
async def prepare_offer_checkout(
    body: OfferCheckoutRequestSchema,
    user: VerifiedUser = Depends(get_current_user),
    use_case: CheckoutPreparationUseCase = Depends(get_checkout_preparation_use_case),
) -> CheckoutResponseSchema:
    try:
        result = await use_case.prepare_offer(
            OfferCheckoutCommand(
                offer_id=body.offer_id,
                requirements=body.requirements,
                brand_user_id=user.id,
                account_type=user.account_type,
            )
        )
    except NotBrandAccountError as error:
        raise HTTPException(status_code=403, detail=str(error))
    except PackageNotOrderableError as error:
        raise HTTPException(status_code=404, detail=str(error))
    return CheckoutResponseSchema(
        pg_order_id=result.pg_order_id,
        amount_krw=result.amount_krw,
        order_name=result.order_name,
        client_key=result.client_key,
    )
