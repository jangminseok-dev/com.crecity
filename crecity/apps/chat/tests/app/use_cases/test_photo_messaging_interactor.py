import pytest

from chat.app.dtos.photo_messaging_dto import SendPhotoCommand
from chat.app.exceptions import ConversationNotFoundError
from chat.app.use_cases.photo_messaging_interactor import PhotoMessagingInteractor
from chat.domain.entities.conversation_entity import Conversation, Message, NotParticipantError
from hub.app.dtos.creator_ref_dto import CreatorRef
from hub.app.dtos.user_ref_dto import UserRef

_PNG = b"\x89PNG fake-bytes"


class _StubConversations:
    def __init__(self, conversation: Conversation | None):
        self.conversation = conversation

    async def find_by_id(self, conversation_id):
        return self.conversation


class _StubMessages:
    def __init__(self, unread: dict[int, int] | None = None):
        self.created: list[dict] = []
        self.published: list = []          # 함께 적재된 알림 이벤트(갭 #72)
        self.unread = unread or {}

    async def unread_counts(self, user_id, conversation_ids):
        return self.unread

    async def create(self, conversation_id, sender_user_id, body, image_file_name=None, events=None):
        self.published += list(events or [])
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


class _StubCreators:
    async def get_creator_by_slug(self, slug):
        raise NotImplementedError

    async def get_creator_by_user_id(self, user_id):
        return CreatorRef(creator_user_id=user_id, slug="kim-beauty", name="김뷰티")


class _StubUsers:
    async def get_user(self, user_id):
        return UserRef(user_id=user_id, name="라이트홈", account_type="BRAND")


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
    interactor = PhotoMessagingInteractor(
        _StubConversations(_conversation()), messages, storage, _StubCreators(), _StubUsers()
    )
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
        _StubConversations(_conversation()), _StubMessages(), storage, _StubCreators(), _StubUsers()
    )
    with pytest.raises(ValueError):
        await interactor.send_photo(_command(content_type="image/gif"))
    assert storage.saved == []  # 검증 실패 시 파일을 만들지 않는다


async def test_대화방이_없으면_ConversationNotFoundError():
    interactor = PhotoMessagingInteractor(
        _StubConversations(None), _StubMessages(), _StubStorage(), _StubCreators(), _StubUsers()
    )
    with pytest.raises(ConversationNotFoundError):
        await interactor.send_photo(_command())


async def test_참여자가_아니면_NotParticipantError():
    interactor = PhotoMessagingInteractor(
        _StubConversations(_conversation(brand=1, creator=2)), _StubMessages(), _StubStorage(),
        _StubCreators(), _StubUsers()
    )
    with pytest.raises(NotParticipantError):
        await interactor.send_photo(_command(sender=99))


async def test_사진_메시지도_새_메시지_알림을_보낸다():
    """텍스트만 알리면 사진 전송이 조용히 묻힌다(갭 #72)."""
    messages = _StubMessages()
    interactor = PhotoMessagingInteractor(
        _StubConversations(_conversation()), messages, _StubStorage(), _StubCreators(), _StubUsers()
    )
    await interactor.send_photo(_command())
    assert len(messages.published) == 1
    assert messages.published[0].payload["recipient_user_id"] == 2


async def test_상대가_아직_안_읽었으면_사진도_추가_알림_없다():
    messages = _StubMessages(unread={10: 3})
    interactor = PhotoMessagingInteractor(
        _StubConversations(_conversation()), messages, _StubStorage(), _StubCreators(), _StubUsers()
    )
    await interactor.send_photo(_command())
    assert messages.published == []
