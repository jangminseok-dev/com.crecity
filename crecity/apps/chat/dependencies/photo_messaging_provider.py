from __future__ import annotations

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from chat.adapter.outbound.local_chat_photo_storage import LocalChatPhotoStorage
from chat.adapter.outbound.pg.conversation_pg_repository import ConversationPgRepository
from chat.adapter.outbound.pg.message_pg_repository import MessagePgRepository
from chat.app.ports.input.photo_messaging_use_case import PhotoMessagingUseCase
from chat.app.use_cases.photo_messaging_interactor import PhotoMessagingInteractor
from core.database import get_db


def get_photo_messaging_use_case(
    db: AsyncSession = Depends(get_db),
) -> PhotoMessagingUseCase:
    return PhotoMessagingInteractor(
        conversations=ConversationPgRepository(session=db),
        messages=MessagePgRepository(session=db),
        storage=LocalChatPhotoStorage(),
    )
