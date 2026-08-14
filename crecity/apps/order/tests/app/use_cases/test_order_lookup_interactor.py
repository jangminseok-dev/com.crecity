from datetime import datetime, timezone

import pytest

from order.app.dtos.order_lookup_dto import MyOrdersQuery, OrderDetailQuery
from order.app.dtos.party_stats_dto import PartyTradeStats
from order.app.exceptions import NotOrderParticipantError, OrderNotFoundError
from order.app.use_cases.order_lookup_interactor import OrderLookupInteractor
from hub.app.dtos.creator_ref_dto import CreatorRef
from hub.app.dtos.user_ref_dto import UserRef
from order.domain.entities.order_entity import Order, OrderStatus

_NOW = datetime(2026, 8, 10, 12, 0, tzinfo=timezone.utc)
BRAND, CREATOR = 100, 200


def _order(id=1):
    return Order(
        id=id,
        package_id=10,
        package_title="릴스 1개",
        brand_user_id=BRAND,
        creator_user_id=CREATOR,
        amount_krw=300000,
        brand_fee_percent=10,
        creator_fee_percent=10,
        requirements="60초 릴스",
        status=OrderStatus.PENDING_ACCEPT,
        deadline_at=_NOW,
    )


_NO_HISTORY = PartyTradeStats(0, 0, 0, 0, 0, 0)


class _StubOrderRepository:
    def __init__(self, orders: list[Order], stats: PartyTradeStats | None = None):
        self.orders = orders
        self.stats = stats or _NO_HISTORY
        self.stats_calls: list[tuple[int, bool]] = []

    async def create(self, order, entries, events):
        raise NotImplementedError

    async def find_by_id(self, order_id):
        return next((o for o in self.orders if o.id == order_id), None)

    async def save_transition(self, order, entries, events):
        raise NotImplementedError

    async def list_by_participant(self, user_id):
        return [o for o in self.orders if user_id in (o.brand_user_id, o.creator_user_id)]

    async def get_party_stats(self, user_id, as_brand):
        self.stats_calls.append((user_id, as_brand))
        return self.stats

    async def find_expired(self, now, limit):
        raise NotImplementedError


class _StubCreators:
    """허브 CreatorRefPort 스텁 — 호출 횟수로 N+1 방지를 확인한다."""

    def __init__(self, ref: CreatorRef | None = None):
        self.ref = ref
        self.calls: list[int] = []

    async def get_creator_by_slug(self, slug):
        raise NotImplementedError

    async def get_creator_by_user_id(self, user_id):
        self.calls.append(user_id)
        return self.ref


class _StubUsers:
    def __init__(self, ref: UserRef | None = None):
        self.ref = ref
        self.calls: list[int] = []

    async def get_user(self, user_id):
        self.calls.append(user_id)
        return self.ref


def _interactor(repository, creators=None, users=None) -> OrderLookupInteractor:
    return OrderLookupInteractor(
        orders=repository,
        creators=creators or _StubCreators(),
        users=users or _StubUsers(),
    )


async def test_내가_참여한_주문만_보인다():
    interactor = _interactor(_StubOrderRepository([_order()]))
    assert len(await interactor.list_my_orders(MyOrdersQuery(user_id=BRAND))) == 1
    assert len(await interactor.list_my_orders(MyOrdersQuery(user_id=CREATOR))) == 1
    assert await interactor.list_my_orders(MyOrdersQuery(user_id=999)) == []


async def test_당사자는_상세를_볼_수_있다():
    interactor = _interactor(_StubOrderRepository([_order()]))
    result = await interactor.get_order(OrderDetailQuery(order_id=1, requester_user_id=CREATOR))
    assert result.id == 1
    assert result.brand_total_krw == 330000


async def test_제3자_상세_조회는_NotOrderParticipantError():
    interactor = _interactor(_StubOrderRepository([_order()]))
    with pytest.raises(NotOrderParticipantError):
        await interactor.get_order(OrderDetailQuery(order_id=1, requester_user_id=999))


async def test_없는_주문이면_OrderNotFoundError():
    interactor = _interactor(_StubOrderRepository([]))
    with pytest.raises(OrderNotFoundError):
        await interactor.get_order(OrderDetailQuery(order_id=99, requester_user_id=BRAND))


async def test_브랜드에게는_크리에이터가_상대로_보인다():
    creators = _StubCreators(CreatorRef(creator_user_id=CREATOR, slug="kim-beauty", name="김뷰티"))
    interactor = _interactor(_StubOrderRepository([_order()]), creators=creators)
    result = await interactor.get_order(OrderDetailQuery(order_id=1, requester_user_id=BRAND))
    assert result.counterpart_name == "김뷰티"
    assert result.counterpart_slug == "kim-beauty"


async def test_크리에이터에게는_브랜드가_상대로_보인다():
    users = _StubUsers(UserRef(user_id=BRAND, name="라이트홈", account_type="BRAND"))
    interactor = _interactor(_StubOrderRepository([_order()]), users=users)
    result = await interactor.get_order(OrderDetailQuery(order_id=1, requester_user_id=CREATOR))
    assert result.counterpart_name == "라이트홈"
    # 브랜드는 공개 프로필이 없으므로 슬러그가 없다
    assert result.counterpart_slug is None


async def test_같은_상대의_주문이_여러_건이어도_한_번만_조회한다():
    creators = _StubCreators(CreatorRef(creator_user_id=CREATOR, slug="kim-beauty", name="김뷰티"))
    orders = _StubOrderRepository([_order(id=1), _order(id=2), _order(id=3)])
    results = await _interactor(orders, creators=creators).list_my_orders(
        MyOrdersQuery(user_id=BRAND)
    )
    assert len(results) == 3
    assert creators.calls == [CREATOR]  # N+1이 아니다


async def test_상대를_못_찾아도_주문은_그대로_보인다():
    # 탈퇴·프로필 삭제로 참조가 끊겨도 조회가 실패하면 안 된다
    result = await _interactor(_StubOrderRepository([_order()])).get_order(
        OrderDetailQuery(order_id=1, requester_user_id=BRAND)
    )
    assert result.id == 1
    assert result.counterpart_name is None


async def test_상대의_거래_이력을_함께_내려준다():
    # 크리에이터가 볼 때 상대(브랜드)의 이력 — 수락 판단 근거(갭 #65)
    stats = PartyTradeStats(
        total_orders=12,
        completed_orders=9,
        cancelled_orders=1,
        refunded_orders=2,
        accept_expired_orders=0,
        total_revisions=14,
    )
    repository = _StubOrderRepository([_order()], stats=stats)
    result = await _interactor(repository).get_order(
        OrderDetailQuery(order_id=1, requester_user_id=CREATOR)
    )
    assert result.counterpart_completed_orders == 9
    assert result.counterpart_cancelled_orders == 1
    assert result.counterpart_total_revisions == 14
    # 상대가 브랜드이므로 브랜드 기준으로 집계해야 한다
    assert repository.stats_calls == [(BRAND, True)]


async def test_거래_이력이_없으면_지표를_비운다():
    # 0건인데 "완료 0건"을 보여주면 신규 상대를 부당하게 나쁘게 보이게 한다
    result = await _interactor(_StubOrderRepository([_order()])).get_order(
        OrderDetailQuery(order_id=1, requester_user_id=CREATOR)
    )
    assert result.counterpart_completed_orders is None
    assert result.counterpart_total_revisions is None


async def test_브랜드가_볼_때는_크리에이터_기준으로_집계한다():
    repository = _StubOrderRepository([_order()], stats=PartyTradeStats(3, 3, 0, 0, 0, 2))
    await _interactor(repository).get_order(
        OrderDetailQuery(order_id=1, requester_user_id=BRAND)
    )
    assert repository.stats_calls == [(CREATOR, False)]
