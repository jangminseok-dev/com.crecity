import pytest

from order.app.dtos.revision_lookup_dto import RevisionListQuery, RevisionRequestResult
from order.app.exceptions import NotOrderParticipantError, OrderNotFoundError
from order.app.use_cases.revision_lookup_interactor import RevisionLookupInteractor
from order.domain.entities.order_entity import Order, OrderStatus

BRAND, CREATOR, STRANGER = 100, 200, 999


def _order():
    return Order(
        id=1,
        package_id=10,
        package_title="릴스 1개",
        brand_user_id=BRAND,
        creator_user_id=CREATOR,
        amount_krw=300000,
        brand_fee_percent=10,
        creator_fee_percent=10,
        requirements="60초 릴스",
        status=OrderStatus.IN_PROGRESS,
        deadline_at=None,
    )


class _StubOrderRepository:
    def __init__(self, order: Order | None):
        self.order = order

    async def find_by_id(self, order_id):
        return self.order if self.order and self.order.id == order_id else None


class _StubRevisionRepository:
    def __init__(self, items):
        self.items = items

    async def list_by_order(self, order_id):
        return self.items


_ITEMS = [
    RevisionRequestResult(id=1, requested_in="DRAFT_REVIEW", comment="초안 색감 조정", created_at=None),
    RevisionRequestResult(id=2, requested_in="IN_REVIEW", comment="자막 오탈자", created_at=None),
]


def _interactor(order, items=_ITEMS):
    return RevisionLookupInteractor(
        orders=_StubOrderRepository(order), revisions=_StubRevisionRepository(items)
    )


async def test_당사자는_수정_요청_이력을_본다():
    result = await _interactor(_order()).list_revisions(
        RevisionListQuery(order_id=1, requester_user_id=BRAND)
    )
    assert [item.comment for item in result] == ["초안 색감 조정", "자막 오탈자"]
    assert result[0].requested_in == "DRAFT_REVIEW"


async def test_제3자는_NotOrderParticipantError():
    with pytest.raises(NotOrderParticipantError):
        await _interactor(_order()).list_revisions(
            RevisionListQuery(order_id=1, requester_user_id=STRANGER)
        )


async def test_없는_주문이면_OrderNotFoundError():
    with pytest.raises(OrderNotFoundError):
        await _interactor(None).list_revisions(
            RevisionListQuery(order_id=9, requester_user_id=BRAND)
        )
