from admin.app.dtos.order_search_dto import OrderSearchQuery
from admin.app.use_cases.order_search_interactor import OrderSearchInteractor
from hub.app.dtos.order_search_dto import AdminOrderSummary, OrderSearchResult


class _StubOrders:
    def __init__(self, items: list[AdminOrderSummary] | None = None, total: int | None = None):
        self.items = items or []
        self.total = total if total is not None else len(self.items)
        self.criteria_calls = []

    async def search_orders(self, criteria) -> OrderSearchResult:
        self.criteria_calls.append(criteria)
        return OrderSearchResult(items=self.items, total=self.total)


def _summary(order_id=1, status="IN_PROGRESS") -> AdminOrderSummary:
    return AdminOrderSummary(
        id=order_id,
        package_title="인스타그램 릴스 1개",
        brand_user_id=11,
        creator_user_id=22,
        amount_krw=300_000,
        status=status,
        accept_expired=False,
        cancel_requested_by=None,
        revisions_used=1,
        revision_limit=2,
        deadline_at=None,
        created_at=None,
    )


async def test_검색_조건을_그대로_포트에_전달한다():
    orders = _StubOrders(items=[_summary()])
    await OrderSearchInteractor(orders=orders).search(
        OrderSearchQuery(order_id=None, status="IN_PROGRESS", user_id=22, limit=20, offset=40)
    )
    criteria = orders.criteria_calls[0]
    assert criteria.status == "IN_PROGRESS"
    assert criteria.user_id == 22
    assert criteria.offset == 40


async def test_limit은_상한_50으로_잘린다():
    orders = _StubOrders()
    await OrderSearchInteractor(orders=orders).search(OrderSearchQuery(limit=500))
    assert orders.criteria_calls[0].limit == 50


async def test_총계와_항목을_그대로_반환한다():
    orders = _StubOrders(items=[_summary(order_id=7)], total=123)
    result = await OrderSearchInteractor(orders=orders).search(OrderSearchQuery())
    assert result.total == 123
    assert result.items[0].id == 7
    assert result.items[0].revisions_used == 1
    assert result.items[0].revision_limit == 2


async def test_결과가_없으면_빈_목록이다():
    result = await OrderSearchInteractor(orders=_StubOrders()).search(OrderSearchQuery(order_id=999))
    assert result.items == []
    assert result.total == 0
