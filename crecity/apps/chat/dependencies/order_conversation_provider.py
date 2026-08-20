from __future__ import annotations

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from chat.adapter.outbound.pg.conversation_pg_repository import ConversationPgRepository
from chat.app.ports.input.order_conversation_use_case import OrderConversationUseCase
from chat.app.use_cases.order_conversation_interactor import OrderConversationInteractor
from core.database import get_db
from hub.dependencies.creator_ref_provider import get_creator_ref_port
from hub.dependencies.order_participants_provider import get_order_participants_port
from hub.dependencies.user_directory_provider import get_user_directory_port


def get_order_conversation_use_case(
    db: AsyncSession = Depends(get_db),
) -> OrderConversationUseCase:
    return OrderConversationInteractor(
        conversations=ConversationPgRepository(session=db),
        order_participants=get_order_participants_port(),
        creators=get_creator_ref_port(),
        users=get_user_directory_port(),
    )
