from fastapi import APIRouter, Depends, HTTPException, UploadFile

from chat.adapter.inbound.api.schemas.messaging_schema import MessageResponseSchema
from chat.app.dtos.photo_messaging_dto import SendPhotoCommand
from chat.app.exceptions import ConversationNotFoundError
from chat.app.ports.input.photo_messaging_use_case import PhotoMessagingUseCase
from chat.dependencies.photo_messaging_provider import get_photo_messaging_use_case
from chat.domain.entities.conversation_entity import NotParticipantError
from hub.app.dtos.verified_user_dto import VerifiedUser
from hub.dependencies.current_user_provider import get_current_user

photo_messaging_router = APIRouter(prefix="/chat", tags=["chat"])


@photo_messaging_router.post(
    "/conversations/{conversation_id}/photos",
    response_model=MessageResponseSchema,
    status_code=201,
)
async def send_photo(
    conversation_id: int,
    file: UploadFile,
    user: VerifiedUser = Depends(get_current_user),
    use_case: PhotoMessagingUseCase = Depends(get_photo_messaging_use_case),
) -> MessageResponseSchema:
    try:
        result = await use_case.send_photo(
            SendPhotoCommand(
                conversation_id=conversation_id,
                sender_user_id=user.id,
                content=await file.read(),
                content_type=file.content_type or "",
            )
        )
    except ConversationNotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error))
    except NotParticipantError as error:
        raise HTTPException(status_code=403, detail=str(error))
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error))
    return MessageResponseSchema(
        id=result.id,
        conversation_id=result.conversation_id,
        sender_user_id=result.sender_user_id,
        body=result.body,
        is_mine=result.is_mine,
        created_at=result.created_at,
        image_url=f"/uploads/chat/{result.image_file_name}" if result.image_file_name else None,
    )
