from fastapi import APIRouter, Depends, HTTPException

from chat.adapter.inbound.api.schemas.conversation_schema import ConversationResponseSchema
from chat.adapter.inbound.api.v1.conversation_opening_router import to_schema
from chat.app.dtos.order_conversation_dto import OpenOrderConversationCommand
from chat.app.exceptions import NotOrderParticipantError, OrderNotFoundError
from chat.app.ports.input.order_conversation_use_case import OrderConversationUseCase
from chat.dependencies.order_conversation_provider import get_order_conversation_use_case
from hub.app.dtos.verified_user_dto import VerifiedUser
from hub.dependencies.current_user_provider import get_current_user

order_conversation_router = APIRouter(prefix="/chat", tags=["chat"])


@order_conversation_router.post(
    "/conversations/order/{order_id}",
    response_model=ConversationResponseSchema,
    status_code=201,
)
async def open_order_conversation(
    order_id: int,
    user: VerifiedUser = Depends(get_current_user),
    use_case: OrderConversationUseCase = Depends(get_order_conversation_use_case),
) -> ConversationResponseSchema:
    """주문 당사자 간 대화 열기(갭 #95) — 크리에이터도 열 수 있다(콜드 DM 아님)."""
    try:
        result = await use_case.open(
            OpenOrderConversationCommand(order_id=order_id, requester_user_id=user.id)
        )
    except OrderNotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error))
    except NotOrderParticipantError as error:
        raise HTTPException(status_code=403, detail=str(error))
    return to_schema(result)
