from __future__ import annotations

from chat.app.dtos.conversation_listing_dto import ConversationResult
from chat.app.dtos.order_conversation_dto import OpenOrderConversationCommand
from chat.app.exceptions import NotOrderParticipantError, OrderNotFoundError
from chat.app.ports.input.order_conversation_use_case import OrderConversationUseCase
from chat.app.ports.output.conversation_repository import ConversationRepository
from hub.app.ports.output.creator_ref_port import CreatorRefPort
from hub.app.ports.output.order_participants_port import OrderParticipantsPort
from hub.app.ports.output.user_directory_port import UserDirectoryPort


class OrderConversationInteractor(OrderConversationUseCase):

    def __init__(
        self,
        conversations: ConversationRepository,
        order_participants: OrderParticipantsPort,
        creators: CreatorRefPort,
        users: UserDirectoryPort,
    ) -> None:
        self._conversations = conversations
        self._order_participants = order_participants
        self._creators = creators
        self._users = users

    async def open(self, command: OpenOrderConversationCommand) -> ConversationResult:
        # 주문·당사자 검증은 order 소유라 허브 계약으로 읽는다(리뷰 자격 검증과 같은 포트)
        participants = await self._order_participants.get_order_participants(command.order_id)
        if participants is None:
            raise OrderNotFoundError(f"주문을 찾을 수 없습니다: {command.order_id}")
        if command.requester_user_id not in (
            participants.brand_user_id,
            participants.creator_user_id,
        ):
            raise NotOrderParticipantError("주문 당사자만 대화를 열 수 있습니다.")

        # 대화는 (브랜드, 크리에이터) 쌍당 1개 — 일반 문의로 이미 열린 방도 그대로 재사용
        conversation = await self._conversations.find_by_pair(
            participants.brand_user_id, participants.creator_user_id
        )
        if conversation is None:
            conversation = await self._conversations.create(
                participants.brand_user_id, participants.creator_user_id
            )

        # 상대 표시는 요청자 기준 — 크리에이터면 프로필, 브랜드면 회원 디렉토리로 해석
        if command.requester_user_id == participants.brand_user_id:
            creator = await self._creators.get_creator_by_user_id(participants.creator_user_id)
            counterpart_name = creator.name if creator else "(탈퇴한 크리에이터)"
            counterpart_slug = creator.slug if creator else None
        else:
            user = await self._users.get_user(participants.brand_user_id)
            counterpart_name = user.name if user else "(탈퇴한 회원)"
            counterpart_slug = None
        return ConversationResult(
            id=conversation.id,
            counterpart_name=counterpart_name,
            counterpart_slug=counterpart_slug,
            last_message=None,
            last_message_at=None,
            unread_count=0,  # 이동 직후 대화방 화면이 실데이터를 다시 읽는다
            created_at=conversation.created_at,
        )
