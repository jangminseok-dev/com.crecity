from __future__ import annotations

from chat.app.dtos.messaging_dto import MessageResult
from chat.app.dtos.photo_messaging_dto import SendPhotoCommand
from chat.app.exceptions import ConversationNotFoundError
from chat.app.message_notifications import build_message_events
from chat.app.ports.input.photo_messaging_use_case import PhotoMessagingUseCase
from chat.app.ports.output.chat_photo_storage import ChatPhotoStorage
from chat.app.ports.output.conversation_repository import ConversationRepository
from chat.app.ports.output.message_repository import MessageRepository
from chat.domain.value_objects.image_file import ImageFile
from hub.app.ports.output.creator_ref_port import CreatorRefPort
from hub.app.ports.output.user_directory_port import UserDirectoryPort


class PhotoMessagingInteractor(PhotoMessagingUseCase):

    def __init__(
        self,
        conversations: ConversationRepository,
        messages: MessageRepository,
        storage: ChatPhotoStorage,
        creators: CreatorRefPort,
        users: UserDirectoryPort,
    ) -> None:
        self._conversations = conversations
        self._messages = messages
        self._storage = storage
        self._creators = creators
        self._users = users

    async def send_photo(self, command: SendPhotoCommand) -> MessageResult:
        image = ImageFile(content=command.content, content_type=command.content_type)

        conversation = await self._conversations.find_by_id(command.conversation_id)
        if conversation is None:
            raise ConversationNotFoundError(f"대화방을 찾을 수 없습니다: {command.conversation_id}")
        conversation.ensure_participant(command.sender_user_id)

        events = await build_message_events(
            conversation, command.sender_user_id, self._messages, self._creators, self._users
        )
        file_name = self._storage.save(image.content, image.extension)
        message = await self._messages.create(
            conversation_id=command.conversation_id,
            sender_user_id=command.sender_user_id,
            body="",  # 사진 전용 메시지 — 본문 없음(목록 미리보기는 조회 측이 처리)
            image_file_name=file_name,
            events=events,
        )
        return MessageResult(
            id=message.id,
            conversation_id=message.conversation_id,
            sender_user_id=message.sender_user_id,
            body=message.body,
            is_mine=True,
            created_at=message.created_at,
            image_file_name=message.image_file_name,
        )
