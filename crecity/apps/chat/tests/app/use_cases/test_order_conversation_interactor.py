import pytest

from chat.app.dtos.order_conversation_dto import OpenOrderConversationCommand
from chat.app.exceptions import NotOrderParticipantError, OrderNotFoundError
from chat.app.use_cases.order_conversation_interactor import OrderConversationInteractor
from chat.domain.entities.conversation_entity import Conversation
from hub.app.dtos.creator_ref_dto import CreatorRef
from hub.app.dtos.order_participants_dto import OrderParticipants
from hub.app.dtos.user_ref_dto import UserRef


class _StubConversations:
    def __init__(self, existing: Conversation | None = None):
        self.existing = existing
        self.created: list[tuple[int, int]] = []

    async def find_by_pair(self, brand_user_id, creator_user_id):
        return self.existing

    async def create(self, brand_user_id, creator_user_id):
        self.created.append((brand_user_id, creator_user_id))
        return Conversation(
            id=77, brand_user_id=brand_user_id, creator_user_id=creator_user_id, created_at=None
        )


class _StubParticipants:
    def __init__(self, participants: OrderParticipants | None):
        self.participants = participants

    async def get_order_participants(self, order_id):
        return self.participants


class _StubCreators:
    async def get_creator_by_user_id(self, user_id):
        return CreatorRef(creator_user_id=user_id, slug="haneul", name="김하늘")


class _StubUsers:
    async def get_user(self, user_id):
        return UserRef(user_id=user_id, name="데모브랜드", account_type="BRAND")


_PARTICIPANTS = OrderParticipants(
    order_id=8, status="IN_PROGRESS", brand_user_id=9, creator_user_id=10
)


def _interactor(conversations=None, participants=_PARTICIPANTS):
    return OrderConversationInteractor(
        conversations=conversations or _StubConversations(),
        order_participants=_StubParticipants(participants),
        creators=_StubCreators(),
        users=_StubUsers(),
    )


async def test_없는_주문은_404_예외():
    with pytest.raises(OrderNotFoundError):
        await _interactor(participants=None).open(
            OpenOrderConversationCommand(order_id=999, requester_user_id=9)
        )


async def test_당사자가_아니면_403_예외():
    with pytest.raises(NotOrderParticipantError):
        await _interactor().open(OpenOrderConversationCommand(order_id=8, requester_user_id=55))


async def test_크리에이터도_열_수_있고_새_대화를_만든다():
    conversations = _StubConversations()
    result = await _interactor(conversations).open(
        OpenOrderConversationCommand(order_id=8, requester_user_id=10)
    )
    assert conversations.created == [(9, 10)]  # (브랜드, 크리에이터) 쌍으로 생성
    assert result.id == 77
    assert result.counterpart_name == "데모브랜드"  # 크리에이터가 열면 상대는 브랜드
    assert result.counterpart_slug is None


async def test_기존_대화가_있으면_재사용한다():
    existing = Conversation(id=3, brand_user_id=9, creator_user_id=10, created_at=None)
    conversations = _StubConversations(existing=existing)
    result = await _interactor(conversations).open(
        OpenOrderConversationCommand(order_id=8, requester_user_id=9)
    )
    assert conversations.created == []
    assert result.id == 3
    assert result.counterpart_name == "김하늘"  # 브랜드가 열면 상대는 크리에이터
    assert result.counterpart_slug == "haneul"
