import pytest

from chat.app.dtos.photo_messaging_dto import SendPhotoCommand
from chat.app.exceptions import ConversationNotFoundError
from chat.app.use_cases.photo_messaging_interactor import PhotoMessagingInteractor
from chat.domain.entities.conversation_entity import Conversation, Message, NotParticipantError

_PNG = b"\x89PNG fake-bytes"


class _StubConversations:
    def __init__(self, conversation: Conversation | None):
        self.conversation = conversation

    async def find_by_id(self, conversation_id):
        return self.conversation


class _StubMessages:
    def __init__(self):
        self.created: list[dict] = []

    async def create(self, conversation_id, sender_user_id, body, image_file_name=None):
        self.created.append(
            {
                "conversation_id": conversation_id,
                "sender_user_id": sender_user_id,
                "body": body,
                "image_file_name": image_file_name,
            }
        )
        return Message(
            id=1,
            conversation_id=conversation_id,
            sender_user_id=sender_user_id,
            body=body,
            image_file_name=image_file_name,
        )


class _StubStorage:
    def __init__(self):
        self.saved: list[tuple[bytes, str]] = []

    def save(self, content, extension):
        self.saved.append((content, extension))
        return f"photo.{extension}"

    def delete(self, file_name):
        raise NotImplementedError


def _conversation(brand=1, creator=2):
    return Conversation(id=10, brand_user_id=brand, creator_user_id=creator)


def _command(sender=1, content=_PNG, content_type="image/png"):
    return SendPhotoCommand(
        conversation_id=10, sender_user_id=sender, content=content, content_type=content_type
    )


async def test_참여자는_사진_메시지를_보낼_수_있다():
    messages = _StubMessages()
    storage = _StubStorage()
    interactor = PhotoMessagingInteractor(_StubConversations(_conversation()), messages, storage)
    result = await interactor.send_photo(_command())
    assert storage.saved == [(_PNG, "png")]
    assert messages.created == [
        {"conversation_id": 10, "sender_user_id": 1, "body": "", "image_file_name": "photo.png"}
    ]
    assert result.image_file_name == "photo.png"
    assert result.is_mine is True


async def test_지원하지_않는_형식은_저장_전에_거부한다():
    storage = _StubStorage()
    interactor = PhotoMessagingInteractor(
        _StubConversations(_conversation()), _StubMessages(), storage
    )
    with pytest.raises(ValueError):
        await interactor.send_photo(_command(content_type="image/gif"))
    assert storage.saved == []  # 검증 실패 시 파일을 만들지 않는다


async def test_대화방이_없으면_ConversationNotFoundError():
    interactor = PhotoMessagingInteractor(_StubConversations(None), _StubMessages(), _StubStorage())
    with pytest.raises(ConversationNotFoundError):
        await interactor.send_photo(_command())


async def test_참여자가_아니면_NotParticipantError():
    interactor = PhotoMessagingInteractor(
        _StubConversations(_conversation(brand=1, creator=2)), _StubMessages(), _StubStorage()
    )
    with pytest.raises(NotParticipantError):
        await interactor.send_photo(_command(sender=99))
