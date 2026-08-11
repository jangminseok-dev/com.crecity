from fastapi import APIRouter, Depends, HTTPException

from hub.app.dtos.verified_user_dto import VerifiedUser
from hub.dependencies.current_user_provider import get_current_user
from payment.adapter.inbound.api.schemas.payment_confirmation_schema import (
    ConfirmRequestSchema,
    ConfirmResponseSchema,
)
from payment.app.dtos.payment_confirmation_dto import ConfirmCommand
from payment.app.exceptions import (
    NotPaymentOwnerError,
    PaymentAlreadyProcessedError,
    PaymentAmountMismatchError,
    PaymentConfirmError,
    PaymentIntentNotFoundError,
)
from payment.app.ports.input.payment_confirmation_use_case import PaymentConfirmationUseCase
from payment.dependencies.payment_confirmation_provider import get_payment_confirmation_use_case

payment_confirmation_router = APIRouter(prefix="/payment", tags=["payment"])


@payment_confirmation_router.post("/confirm", response_model=ConfirmResponseSchema)
async def confirm_payment(
    body: ConfirmRequestSchema,
    user: VerifiedUser = Depends(get_current_user),
    use_case: PaymentConfirmationUseCase = Depends(get_payment_confirmation_use_case),
) -> ConfirmResponseSchema:
    try:
        result = await use_case.confirm(
            ConfirmCommand(
                payment_key=body.payment_key,
                pg_order_id=body.pg_order_id,
                amount_krw=body.amount_krw,
                requester_user_id=user.id,
            )
        )
    except PaymentIntentNotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error))
    except NotPaymentOwnerError as error:
        raise HTTPException(status_code=403, detail=str(error))
    except PaymentAlreadyProcessedError as error:
        raise HTTPException(status_code=409, detail=str(error))
    except PaymentAmountMismatchError as error:
        raise HTTPException(status_code=400, detail=str(error))
    except PaymentConfirmError as error:
        raise HTTPException(status_code=502, detail=str(error))
    return ConfirmResponseSchema(order_id=result.order_id, order_ids=list(result.order_ids))
