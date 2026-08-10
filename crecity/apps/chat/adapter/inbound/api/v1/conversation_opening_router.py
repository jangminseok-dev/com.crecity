from fastapi import APIRouter, Depends, HTTPException

from chat.adapter.inbound.api.schemas.conversation_schema import (
    ConversationResponseSchema,
    OpenConversationRequestSchema,
)
from chat.app.dtos.conversation_opening_dto import OpenConversationCommand
from chat.app.exceptions import CreatorNotFoundError, NotBrandAccountError
from chat.app.ports.input.conversation_opening_use_case import ConversationOpeningUseCase
from chat.dependencies.conversation_opening_provider import get_conversation_opening_use_case
from hub.app.dtos.verified_user_dto import VerifiedUser
from hub.dependencies.current_user_provider import get_current_user

conversation_opening_router = APIRouter(prefix="/chat", tags=["chat"])


def to_schema(result) -> ConversationResponseSchema:
    return ConversationResponseSchema(
        id=result.id,
        counterpart_name=result.counterpart_name,
        counterpart_slug=result.counterpart_slug,
        last_message=result.last_message,
        last_message_at=result.last_message_at,
        created_at=result.created_at,
    )


@conversation_opening_router.post(
    "/conversations", response_model=ConversationResponseSchema, status_code=201
)
async def open_conversation(
    body: OpenConversationRequestSchema,
    user: VerifiedUser = Depends(get_current_user),
    use_case: ConversationOpeningUseCase = Depends(get_conversation_opening_use_case),
) -> ConversationResponseSchema:
    try:
        result = await use_case.open(
            OpenConversationCommand(
                creator_slug=body.creator_slug,
                brand_user_id=user.id,
                account_type=user.account_type,
            )
        )
    except NotBrandAccountError as error:
        raise HTTPException(status_code=403, detail=str(error))
    except CreatorNotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error))
    return to_schema(result)
