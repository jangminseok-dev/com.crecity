from __future__ import annotations

from chat.app.dtos.conversation_listing_dto import ConversationResult
from chat.app.dtos.conversation_opening_dto import OpenConversationCommand
from chat.app.exceptions import CreatorNotFoundError, NotBrandAccountError
from chat.app.ports.input.conversation_opening_use_case import ConversationOpeningUseCase
from chat.app.ports.output.conversation_repository import ConversationRepository
from hub.app.ports.output.creator_ref_port import CreatorRefPort


class ConversationOpeningInteractor(ConversationOpeningUseCase):

    def __init__(self, conversations: ConversationRepository, creators: CreatorRefPort) -> None:
        self._conversations = conversations
        self._creators = creators

    async def open(self, command: OpenConversationCommand) -> ConversationResult:
        if command.account_type != "BRAND":
            raise NotBrandAccountError("브랜드 계정만 문의를 시작할 수 있습니다.")
        creator = await self._creators.get_creator_by_slug(command.creator_slug)
        if creator is None:
            raise CreatorNotFoundError(f"크리에이터를 찾을 수 없습니다: {command.creator_slug}")

        conversation = await self._conversations.find_by_pair(
            command.brand_user_id, creator.creator_user_id
        )
        if conversation is None:
            conversation = await self._conversations.create(
                command.brand_user_id, creator.creator_user_id
            )
        return ConversationResult(
            id=conversation.id,
            counterpart_name=creator.name,
            counterpart_slug=creator.slug,
            last_message=None,
            last_message_at=None,
            created_at=conversation.created_at,
        )
