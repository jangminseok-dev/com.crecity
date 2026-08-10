from __future__ import annotations

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from chat.adapter.outbound.pg.conversation_pg_repository import ConversationPgRepository
from chat.app.ports.input.conversation_opening_use_case import ConversationOpeningUseCase
from chat.app.use_cases.conversation_opening_interactor import ConversationOpeningInteractor
from core.database import get_db
from hub.dependencies.creator_ref_provider import get_creator_ref_port


def get_conversation_opening_use_case(
    db: AsyncSession = Depends(get_db),
) -> ConversationOpeningUseCase:
    return ConversationOpeningInteractor(
        conversations=ConversationPgRepository(session=db),
        creators=get_creator_ref_port(),
    )
