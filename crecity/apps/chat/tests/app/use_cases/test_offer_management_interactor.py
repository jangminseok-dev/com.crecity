import pytest

from chat.app.dtos.offer_management_dto import OfferCreationCommand, OffersQuery
from chat.app.exceptions import ConversationNotFoundError, NotConversationCreatorError
from chat.app.use_cases.offer_management_interactor import OfferManagementInteractor
from chat.domain.entities.conversation_entity import Conversation, NotParticipantError
from chat.domain.entities.custom_offer_entity import CustomOffer, OfferStatus

BRAND, CREATOR, STRANGER = 1, 2, 99


class _StubConversationRepository:
    def __init__(self, conversation):
        self.conversation = conversation

    async def find_by_id(self, conversation_id):
        if self.conversation and self.conversation.id == conversation_id:
            return self.conversation
        return None


class _StubOfferRepository:
    def __init__(self, offers=None):
        self.offers = list(offers or [])

    async def create(self, conversation_id, title, price_krw, revision_limit, usage_rights):
        offer = CustomOffer(
            id=len(self.offers) + 1, conversation_id=conversation_id,
            title=title, price_krw=price_krw, status=OfferStatus.PENDING,
            revision_limit=revision_limit, usage_rights=usage_rights,
        )
        self.offers.append(offer)
        return offer

    async def list_by_conversation(self, conversation_id):
        return [o for o in self.offers if o.conversation_id == conversation_id]


def _interactor(offers=None):
    conversation = Conversation(id=7, brand_user_id=BRAND, creator_user_id=CREATOR)
    offer_repo = _StubOfferRepository(offers)
    return OfferManagementInteractor(_StubConversationRepository(conversation), offer_repo)


def _create(
    user_id=CREATOR, title="맞춤 릴스 2건", price=450000, conversation_id=7,
    revision_limit=2, usage_rights="",
):
    return OfferCreationCommand(
        conversation_id=conversation_id, title=title, price_krw=price,
        revision_limit=revision_limit, usage_rights=usage_rights,
        requester_user_id=user_id,
    )


async def test_합의_조건이_오퍼에_실린다():
    interactor = _interactor()
    result = await interactor.create(
        _create(revision_limit=5, usage_rights="SNS 게시 6개월")
    )
    assert result.revision_limit == 5
    assert result.usage_rights == "SNS 게시 6개월"


async def test_수정_횟수_범위_밖은_거부된다():
    with pytest.raises(ValueError):
        await _interactor().create(_create(revision_limit=11))


async def test_사용권_길이_초과는_거부된다():
    with pytest.raises(ValueError):
        await _interactor().create(_create(usage_rights="가" * 301))


async def test_크리에이터는_오퍼를_보낼_수_있다():
    result = await _interactor().create(_create())
    assert result.status == "PENDING"
    assert result.price_krw == 450000


async def test_브랜드는_오퍼를_보낼_수_없다():
    with pytest.raises(NotConversationCreatorError):
        await _interactor().create(_create(user_id=BRAND))


async def test_없는_대화에는_보낼_수_없다():
    with pytest.raises(ConversationNotFoundError):
        await _interactor().create(_create(conversation_id=99))


async def test_가격이_0이하면_거부된다():
    with pytest.raises(ValueError):
        await _interactor().create(_create(price=0))


async def test_빈_제목은_거부된다():
    with pytest.raises(ValueError):
        await _interactor().create(_create(title="   "))


async def test_당사자는_오퍼_목록을_본다():
    offers = [CustomOffer(id=1, conversation_id=7, title="t", price_krw=1000,
                          status=OfferStatus.PENDING)]
    results = await _interactor(offers).list_for_conversation(
        OffersQuery(conversation_id=7, requester_user_id=BRAND)
    )
    assert len(results) == 1


async def test_제삼자는_오퍼_목록을_볼_수_없다():
    with pytest.raises(NotParticipantError):
        await _interactor().list_for_conversation(
            OffersQuery(conversation_id=7, requester_user_id=STRANGER)
        )
