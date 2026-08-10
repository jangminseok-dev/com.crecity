"""chat 3개 유스케이스(개설·목록·메시징)의 스텁 검증 — 공용 스텁을 공유한다."""

import pytest

from chat.app.dtos.conversation_opening_dto import OpenConversationCommand
from chat.app.dtos.messaging_dto import MessagesQuery, SendMessageCommand
from chat.app.exceptions import (
    ConversationNotFoundError,
    CreatorNotFoundError,
    NotBrandAccountError,
)
from chat.app.use_cases.conversation_listing_interactor import ConversationListingInteractor
from chat.app.use_cases.conversation_opening_interactor import ConversationOpeningInteractor
from chat.app.use_cases.messaging_interactor import MessagingInteractor
from chat.domain.entities.conversation_entity import (
    Conversation,
    Message,
    NotParticipantError,
)
from hub.app.dtos.creator_ref_dto import CreatorRef
from hub.app.dtos.user_ref_dto import UserRef

BRAND, CREATOR = 100, 200
_REF = CreatorRef(creator_user_id=CREATOR, slug="kim-beauty", name="김뷰티")


class _StubConversationRepository:
    def __init__(self, conversations: list[Conversation] | None = None):
        self.conversations = list(conversations or [])

    async def create(self, brand_user_id, creator_user_id):
        conversation = Conversation(
            id=len(self.conversations) + 1,
            brand_user_id=brand_user_id,
            creator_user_id=creator_user_id,
        )
        self.conversations.append(conversation)
        return conversation

    async def find_by_pair(self, brand_user_id, creator_user_id):
        return next(
            (c for c in self.conversations
             if c.brand_user_id == brand_user_id and c.creator_user_id == creator_user_id),
            None,
        )

    async def find_by_id(self, conversation_id):
        return next((c for c in self.conversations if c.id == conversation_id), None)

    async def list_by_participant(self, user_id):
        return [c for c in self.conversations if c.is_participant(user_id)]


class _StubMessageRepository:
    def __init__(self):
        self.messages: list[Message] = []

    async def create(self, conversation_id, sender_user_id, body):
        message = Message(
            id=len(self.messages) + 1, conversation_id=conversation_id,
            sender_user_id=sender_user_id, body=body,
        )
        self.messages.append(message)
        return message

    async def list_by_conversation(self, conversation_id, limit):
        return [m for m in self.messages if m.conversation_id == conversation_id][-limit:]

    async def last_by_conversation(self, conversation_id):
        found = [m for m in self.messages if m.conversation_id == conversation_id]
        return found[-1] if found else None


class _StubCreatorRefPort:
    async def get_creator_by_slug(self, slug):
        return _REF if slug == "kim-beauty" else None

    async def get_creator_by_user_id(self, user_id):
        return _REF if user_id == CREATOR else None


class _StubUserDirectoryPort:
    async def get_user(self, user_id):
        return UserRef(user_id=user_id, name="브랜드컴퍼니", account_type="BRAND")


def _conversation():
    return Conversation(id=1, brand_user_id=BRAND, creator_user_id=CREATOR)


# ── 개설 ──────────────────────────────────────────────────────────────────


async def test_브랜드가_문의를_시작하면_대화방이_생긴다():
    repo = _StubConversationRepository()
    interactor = ConversationOpeningInteractor(repo, _StubCreatorRefPort())
    result = await interactor.open(
        OpenConversationCommand(creator_slug="kim-beauty", brand_user_id=BRAND, account_type="BRAND")
    )
    assert result.counterpart_name == "김뷰티"
    assert len(repo.conversations) == 1


async def test_같은_쌍이면_기존_대화방을_재사용한다():
    repo = _StubConversationRepository([_conversation()])
    interactor = ConversationOpeningInteractor(repo, _StubCreatorRefPort())
    result = await interactor.open(
        OpenConversationCommand(creator_slug="kim-beauty", brand_user_id=BRAND, account_type="BRAND")
    )
    assert result.id == 1
    assert len(repo.conversations) == 1  # 새로 만들지 않는다


async def test_크리에이터_계정의_개설은_NotBrandAccountError():
    interactor = ConversationOpeningInteractor(_StubConversationRepository(), _StubCreatorRefPort())
    with pytest.raises(NotBrandAccountError):
        await interactor.open(
            OpenConversationCommand(creator_slug="kim-beauty", brand_user_id=CREATOR, account_type="CREATOR")
        )


async def test_없는_크리에이터면_CreatorNotFoundError():
    interactor = ConversationOpeningInteractor(_StubConversationRepository(), _StubCreatorRefPort())
    with pytest.raises(CreatorNotFoundError):
        await interactor.open(
            OpenConversationCommand(creator_slug="no-one", brand_user_id=BRAND, account_type="BRAND")
        )


# ── 목록 ──────────────────────────────────────────────────────────────────


async def test_상대_이름은_역할에_맞게_해석된다():
    interactor = ConversationListingInteractor(
        _StubConversationRepository([_conversation()]),
        _StubMessageRepository(),
        _StubCreatorRefPort(),
        _StubUserDirectoryPort(),
    )
    brand_view = await interactor.list_mine(BRAND)
    creator_view = await interactor.list_mine(CREATOR)
    assert brand_view[0].counterpart_name == "김뷰티"  # 브랜드가 보면 상대=크리에이터
    assert brand_view[0].counterpart_slug == "kim-beauty"
    assert creator_view[0].counterpart_name == "브랜드컴퍼니"  # 크리에이터가 보면 상대=브랜드


async def test_참여자가_아니면_상세_조회_403():
    interactor = ConversationListingInteractor(
        _StubConversationRepository([_conversation()]),
        _StubMessageRepository(),
        _StubCreatorRefPort(),
        _StubUserDirectoryPort(),
    )
    with pytest.raises(NotParticipantError):
        await interactor.get_conversation(1, 999)


# ── 메시징 ────────────────────────────────────────────────────────────────


async def test_참여자는_메시지를_보내고_받는다():
    conversations = _StubConversationRepository([_conversation()])
    messages = _StubMessageRepository()
    interactor = MessagingInteractor(conversations, messages)

    sent = await interactor.send(SendMessageCommand(conversation_id=1, sender_user_id=BRAND, body="  안녕하세요!  "))
    assert sent.body == "안녕하세요!"  # 공백 정리
    assert sent.is_mine is True

    received = await interactor.list_messages(MessagesQuery(conversation_id=1, requester_user_id=CREATOR))
    assert received[0].body == "안녕하세요!"
    assert received[0].is_mine is False  # 상대 기준


async def test_참여자가_아니면_전송_403():
    interactor = MessagingInteractor(_StubConversationRepository([_conversation()]), _StubMessageRepository())
    with pytest.raises(NotParticipantError):
        await interactor.send(SendMessageCommand(conversation_id=1, sender_user_id=999, body="침입"))


async def test_빈_메시지는_ValueError():
    interactor = MessagingInteractor(_StubConversationRepository([_conversation()]), _StubMessageRepository())
    with pytest.raises(ValueError):
        await interactor.send(SendMessageCommand(conversation_id=1, sender_user_id=BRAND, body="   "))


async def test_없는_대화방이면_ConversationNotFoundError():
    interactor = MessagingInteractor(_StubConversationRepository(), _StubMessageRepository())
    with pytest.raises(ConversationNotFoundError):
        await interactor.list_messages(MessagesQuery(conversation_id=9, requester_user_id=BRAND))
