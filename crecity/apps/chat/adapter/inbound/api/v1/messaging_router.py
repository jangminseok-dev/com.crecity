from fastapi import APIRouter, Depends, HTTPException

from chat.adapter.inbound.api.schemas.messaging_schema import (
    MessageResponseSchema,
    SendMessageRequestSchema,
)
from chat.app.dtos.messaging_dto import MessagesQuery, SendMessageCommand
from chat.app.exceptions import ConversationNotFoundError
from chat.app.ports.input.messaging_use_case import MessagingUseCase
from chat.dependencies.messaging_provider import get_messaging_use_case
from chat.domain.entities.conversation_entity import NotParticipantError
from hub.app.dtos.verified_user_dto import VerifiedUser
from hub.dependencies.current_user_provider import get_current_user

messaging_router = APIRouter(prefix="/chat", tags=["chat"])


def _to_schema(result) -> MessageResponseSchema:
    return MessageResponseSchema(
        id=result.id,
        conversation_id=result.conversation_id,
        sender_user_id=result.sender_user_id,
        body=result.body,
        is_mine=result.is_mine,
        created_at=result.created_at,
    )


@messaging_router.post(
    "/conversations/{conversation_id}/messages",
    response_model=MessageResponseSchema,
    status_code=201,
)
async def send_message(
    conversation_id: int,
    body: SendMessageRequestSchema,
    user: VerifiedUser = Depends(get_current_user),
    use_case: MessagingUseCase = Depends(get_messaging_use_case),
) -> MessageResponseSchema:
    try:
        result = await use_case.send(
            SendMessageCommand(
                conversation_id=conversation_id, sender_user_id=user.id, body=body.body
            )
        )
    except ConversationNotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error))
    except NotParticipantError as error:
        raise HTTPException(status_code=403, detail=str(error))
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error))
    return _to_schema(result)


@messaging_router.get(
    "/conversations/{conversation_id}/messages", response_model=list[MessageResponseSchema]
)
async def list_messages(
    conversation_id: int,
    user: VerifiedUser = Depends(get_current_user),
    use_case: MessagingUseCase = Depends(get_messaging_use_case),
) -> list[MessageResponseSchema]:
    try:
        results = await use_case.list_messages(
            MessagesQuery(conversation_id=conversation_id, requester_user_id=user.id)
        )
    except ConversationNotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error))
    except NotParticipantError as error:
        raise HTTPException(status_code=403, detail=str(error))
    return [_to_schema(result) for result in results]
