from __future__ import annotations

from chat.app.dtos.conversation_listing_dto import ConversationResult
from chat.app.exceptions import ConversationNotFoundError
from chat.app.ports.input.conversation_listing_use_case import ConversationListingUseCase
from chat.app.ports.output.conversation_repository import ConversationRepository
from chat.app.ports.output.message_repository import MessageRepository
from chat.domain.entities.conversation_entity import Conversation
from hub.app.ports.output.creator_ref_port import CreatorRefPort
from hub.app.ports.output.user_directory_port import UserDirectoryPort


class ConversationListingInteractor(ConversationListingUseCase):

    def __init__(
        self,
        conversations: ConversationRepository,
        messages: MessageRepository,
        creators: CreatorRefPort,
        users: UserDirectoryPort,
    ) -> None:
        self._conversations = conversations
        self._messages = messages
        self._creators = creators
        self._users = users

    async def _to_result(
        self, conversation: Conversation, viewer_user_id: int, unread: int = 0
    ) -> ConversationResult:
        counterpart_id = conversation.counterpart_of(viewer_user_id)
        # 상대가 크리에이터면 프로필(이름·슬러그), 아니면 회원 디렉토리(이름)로 해석
        counterpart_slug = None
        if counterpart_id == conversation.creator_user_id:
            creator = await self._creators.get_creator_by_user_id(counterpart_id)
            counterpart_name = creator.name if creator else "(탈퇴한 크리에이터)"
            counterpart_slug = creator.slug if creator else None
        else:
            user = await self._users.get_user(counterpart_id)
            counterpart_name = user.name if user else "(탈퇴한 회원)"
        last = await self._messages.last_by_conversation(conversation.id)
        # 사진 전용 메시지(본문 없음)는 미리보기 문구로 대체
        last_preview = None
        if last:
            last_preview = last.body or ("📷 사진" if last.image_file_name else "")
        return ConversationResult(
            id=conversation.id,
            counterpart_name=counterpart_name,
            counterpart_slug=counterpart_slug,
            last_message=last_preview,
            last_message_at=last.created_at if last else None,
            unread_count=unread,
            created_at=conversation.created_at,
        )

    async def list_mine(self, user_id: int) -> list[ConversationResult]:
        conversations = await self._conversations.list_by_participant(user_id)
        unread = await self._messages.unread_counts(user_id, [c.id for c in conversations])
        results = [
            await self._to_result(c, user_id, unread.get(c.id, 0)) for c in conversations
        ]

        # 마지막 메시지 시각 내림차순(메시지 없으면 생성 시각)
        def recency(result: ConversationResult) -> float:
            moment = result.last_message_at or result.created_at
            return moment.timestamp() if moment else 0.0

        results.sort(key=recency, reverse=True)
        return results

    async def get_conversation(self, conversation_id: int, requester_user_id: int) -> ConversationResult:
        conversation = await self._conversations.find_by_id(conversation_id)
        if conversation is None:
            raise ConversationNotFoundError(f"대화방을 찾을 수 없습니다: {conversation_id}")
        conversation.ensure_participant(requester_user_id)
        return await self._to_result(conversation, requester_user_id)

    async def mark_read(self, conversation_id: int, requester_user_id: int) -> None:
        conversation = await self._conversations.find_by_id(conversation_id)
        if conversation is None:
            raise ConversationNotFoundError(f"대화방을 찾을 수 없습니다: {conversation_id}")
        conversation.ensure_participant(requester_user_id)  # 참여자 검증은 도메인
        await self._messages.mark_read(conversation_id, requester_user_id)
