from __future__ import annotations

from chat.app.dtos.messaging_dto import MessageResult, MessagesQuery, SendMessageCommand
from chat.app.exceptions import ConversationNotFoundError
from chat.app.ports.input.messaging_use_case import MessagingUseCase
from chat.app.ports.output.conversation_repository import ConversationRepository
from chat.app.ports.output.message_repository import MessageRepository
from chat.domain.entities.conversation_entity import Message

_MESSAGE_LIMIT = 100


class MessagingInteractor(MessagingUseCase):

    def __init__(self, conversations: ConversationRepository, messages: MessageRepository) -> None:
        self._conversations = conversations
        self._messages = messages

    def _to_result(self, message: Message, requester_user_id: int) -> MessageResult:
        return MessageResult(
            id=message.id,
            conversation_id=message.conversation_id,
            sender_user_id=message.sender_user_id,
            body=message.body,
            is_mine=message.sender_user_id == requester_user_id,
            created_at=message.created_at,
            image_file_name=message.image_file_name,
        )

    async def _participant_conversation(self, conversation_id: int, user_id: int):
        conversation = await self._conversations.find_by_id(conversation_id)
        if conversation is None:
            raise ConversationNotFoundError(f"대화방을 찾을 수 없습니다: {conversation_id}")
        conversation.ensure_participant(user_id)
        return conversation

    async def send(self, command: SendMessageCommand) -> MessageResult:
        body = command.body.strip()
        if not body:
            raise ValueError("메시지 내용을 입력해 주세요.")
        await self._participant_conversation(command.conversation_id, command.sender_user_id)
        message = await self._messages.create(
            conversation_id=command.conversation_id,
            sender_user_id=command.sender_user_id,
            body=body,
        )
        return self._to_result(message, command.sender_user_id)

    async def list_messages(self, query: MessagesQuery) -> list[MessageResult]:
        await self._participant_conversation(query.conversation_id, query.requester_user_id)
        messages = await self._messages.list_by_conversation(query.conversation_id, _MESSAGE_LIMIT)
        return [self._to_result(message, query.requester_user_id) for message in messages]
