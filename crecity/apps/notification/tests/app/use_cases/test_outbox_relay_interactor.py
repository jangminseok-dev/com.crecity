from notification.app.dtos.outbox_relay_dto import OutboxRecord
from notification.app.use_cases.outbox_relay_interactor import OutboxRelayInteractor

BRAND, CREATOR = 100, 200


class _StubRelayStore:
    def __init__(self, records: list[OutboxRecord]):
        self.records = records
        self.published = []  # (event_ids, drafts)

    async def fetch_unpublished(self, limit):
        return self.records[:limit]

    async def publish(self, event_ids, drafts):
        self.published.append((event_ids, drafts))


def _record(id=1, event_type="order.placed", **extra):
    payload = {
        "order_id": 7, "package_title": "릴스 1개",
        "brand_user_id": BRAND, "creator_user_id": CREATOR, **extra,
    }
    return OutboxRecord(id=id, event_type=event_type, payload=payload)


async def test_주문_생성_이벤트는_크리에이터에게_알림이_된다():
    store = _StubRelayStore([_record()])
    result = await OutboxRelayInteractor(store).relay()
    event_ids, drafts = store.published[0]
    assert event_ids == [1]
    assert drafts[0].user_id == CREATOR
    assert "새 주문" in drafts[0].body
    assert drafts[0].link == "/dashboard/orders/7"
    assert result.created_notifications == 1


async def test_수신자_라우팅_이벤트별로_올바르다():
    cases = {
        "order.accepted": BRAND,
        "order.rejected": BRAND,
        "order.submitted": BRAND,
        "order.revision_requested": CREATOR,
        "order.completed": CREATOR,
    }
    for event_type, recipient in cases.items():
        store = _StubRelayStore([_record(event_type=event_type, payout_krw=270000)])
        await OutboxRelayInteractor(store).relay()
        assert store.published[0][1][0].user_id == recipient, event_type


async def test_완료_알림에는_적립액이_실린다():
    store = _StubRelayStore([_record(event_type="order.completed", payout_krw=270000)])
    await OutboxRelayInteractor(store).relay()
    assert "270,000원 적립" in store.published[0][1][0].body


async def test_심사_이벤트는_프로필_링크로_안내한다():
    record = OutboxRecord(
        id=1, event_type="profile.approved",
        payload={"profile_id": 1, "creator_user_id": CREATOR, "slug": "kim", "name": "김뷰티"},
    )
    store = _StubRelayStore([record])
    await OutboxRelayInteractor(store).relay()
    draft = store.published[0][1][0]
    assert draft.user_id == CREATOR
    assert draft.link == "/dashboard/profile"


async def test_모르는_이벤트는_알림_없이_발행_마킹만_된다():
    store = _StubRelayStore([_record(event_type="future.unknown")])
    result = await OutboxRelayInteractor(store).relay()
    event_ids, drafts = store.published[0]
    assert event_ids == [1]  # 재처리 루프 방지 — 마킹은 된다
    assert drafts == []
    assert result.consumed_events == 1
    assert result.created_notifications == 0


async def test_미발행이_없으면_아무_일도_없다():
    store = _StubRelayStore([])
    result = await OutboxRelayInteractor(store).relay()
    assert store.published == []
    assert result.consumed_events == 0
