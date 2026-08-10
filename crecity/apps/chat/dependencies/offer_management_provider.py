from __future__ import annotations

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from chat.adapter.outbound.pg.conversation_pg_repository import ConversationPgRepository
from chat.adapter.outbound.pg.custom_offer_pg_repository import CustomOfferPgRepository
from chat.app.ports.input.offer_management_use_case import OfferManagementUseCase
from chat.app.use_cases.offer_management_interactor import OfferManagementInteractor
from core.database import get_db


def get_offer_management_use_case(
    db: AsyncSession = Depends(get_db),
) -> OfferManagementUseCase:
    return OfferManagementInteractor(
        conversations=ConversationPgRepository(session=db),
        offers=CustomOfferPgRepository(session=db),
    )
