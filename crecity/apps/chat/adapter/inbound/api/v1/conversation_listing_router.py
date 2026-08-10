from fastapi import APIRouter, Depends, HTTPException

from chat.adapter.inbound.api.schemas.conversation_schema import ConversationResponseSchema
from chat.adapter.inbound.api.v1.conversation_opening_router import to_schema
from chat.app.exceptions import ConversationNotFoundError
from chat.app.ports.input.conversation_listing_use_case import ConversationListingUseCase
from chat.dependencies.conversation_listing_provider import get_conversation_listing_use_case
from chat.domain.entities.conversation_entity import NotParticipantError
from hub.app.dtos.verified_user_dto import VerifiedUser
from hub.dependencies.current_user_provider import get_current_user

conversation_listing_router = APIRouter(prefix="/chat", tags=["chat"])


@conversation_listing_router.get("/conversations", response_model=list[ConversationResponseSchema])
async def list_my_conversations(
    user: VerifiedUser = Depends(get_current_user),
    use_case: ConversationListingUseCase = Depends(get_conversation_listing_use_case),
) -> list[ConversationResponseSchema]:
    results = await use_case.list_mine(user.id)
    return [to_schema(result) for result in results]


@conversation_listing_router.get(
    "/conversations/{conversation_id}", response_model=ConversationResponseSchema
)
async def get_conversation(
    conversation_id: int,
    user: VerifiedUser = Depends(get_current_user),
    use_case: ConversationListingUseCase = Depends(get_conversation_listing_use_case),
) -> ConversationResponseSchema:
    try:
        result = await use_case.get_conversation(conversation_id, user.id)
    except ConversationNotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error))
    except NotParticipantError as error:
        raise HTTPException(status_code=403, detail=str(error))
    return to_schema(result)
