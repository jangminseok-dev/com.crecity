from __future__ import annotations

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from chat.adapter.outbound.pg.conversation_pg_repository import ConversationPgRepository
from chat.adapter.outbound.pg.message_pg_repository import MessagePgRepository
from chat.app.ports.input.messaging_use_case import MessagingUseCase
from chat.app.use_cases.messaging_interactor import MessagingInteractor
from core.database import get_db
from hub.dependencies.creator_ref_provider import get_creator_ref_port
from hub.dependencies.user_directory_provider import get_user_directory_port


def get_messaging_use_case(
    db: AsyncSession = Depends(get_db),
) -> MessagingUseCase:
    return MessagingInteractor(
        conversations=ConversationPgRepository(session=db),
        messages=MessagePgRepository(session=db),
        creators=get_creator_ref_port(),
        users=get_user_directory_port(),
    )
