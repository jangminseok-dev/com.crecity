from fastapi import APIRouter, Depends, HTTPException

from chat.adapter.inbound.api.schemas.offer_management_schema import (
    OfferCreateRequestSchema,
    OfferResponseSchema,
)
from chat.app.dtos.offer_management_dto import OfferCreationCommand, OffersQuery
from chat.app.exceptions import ConversationNotFoundError, NotConversationCreatorError
from chat.app.ports.input.offer_management_use_case import OfferManagementUseCase
from chat.dependencies.offer_management_provider import get_offer_management_use_case
from chat.domain.entities.conversation_entity import NotParticipantError
from hub.app.dtos.verified_user_dto import VerifiedUser
from hub.dependencies.current_user_provider import get_current_user

offer_management_router = APIRouter(prefix="/chat", tags=["chat"])


def _to_schema(result) -> OfferResponseSchema:
    return OfferResponseSchema(
        id=result.id,
        conversation_id=result.conversation_id,
        title=result.title,
        price_krw=result.price_krw,
        status=result.status,
        order_id=result.order_id,
        created_at=result.created_at,
    )


@offer_management_router.post(
    "/conversations/{conversation_id}/offers",
    response_model=OfferResponseSchema,
    status_code=201,
)
async def create_offer(
    conversation_id: int,
    body: OfferCreateRequestSchema,
    user: VerifiedUser = Depends(get_current_user),
    use_case: OfferManagementUseCase = Depends(get_offer_management_use_case),
) -> OfferResponseSchema:
    try:
        result = await use_case.create(
            OfferCreationCommand(
                conversation_id=conversation_id,
                title=body.title,
                price_krw=body.price_krw,
                requester_user_id=user.id,
            )
        )
    except ConversationNotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error))
    except NotConversationCreatorError as error:
        raise HTTPException(status_code=403, detail=str(error))
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error))
    return _to_schema(result)


@offer_management_router.get(
    "/conversations/{conversation_id}/offers", response_model=list[OfferResponseSchema]
)
async def list_offers(
    conversation_id: int,
    user: VerifiedUser = Depends(get_current_user),
    use_case: OfferManagementUseCase = Depends(get_offer_management_use_case),
) -> list[OfferResponseSchema]:
    try:
        results = await use_case.list_for_conversation(
            OffersQuery(conversation_id=conversation_id, requester_user_id=user.id)
        )
    except ConversationNotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error))
    except NotParticipantError as error:
        raise HTTPException(status_code=403, detail=str(error))
    return [_to_schema(result) for result in results]
