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
        "order.draft_submitted": BRAND,  # 초안 컨펌은 브랜드 몫(갭 #85)
        "order.draft_approved": CREATOR,  # 컨펌·자동 컨펌 모두 크리에이터가 이어받는다
        "review.brand_received": BRAND,  # 브랜드 평가(갭 #83)
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


async def test_취소_요청_알림은_요청자의_상대방에게_간다():
    for requested_by, recipient in [(BRAND, CREATOR), (CREATOR, BRAND)]:
        store = _StubRelayStore(
            [_record(event_type="order.cancel_requested", requested_by=requested_by)]
        )
        await OutboxRelayInteractor(store).relay()
        assert store.published[0][1][0].user_id == recipient, requested_by


async def test_합의_취소_알림은_양측_모두에게_간다():
    store = _StubRelayStore([_record(event_type="order.cancelled")])
    await OutboxRelayInteractor(store).relay()
    drafts = store.published[0][1]
    assert {d.user_id for d in drafts} == {BRAND, CREATOR}
    assert "환불" in next(d.body for d in drafts if d.user_id == BRAND)


async def test_취소_거부_알림은_요청자에게_간다():
    store = _StubRelayStore([_record(event_type="order.cancel_declined", requested_by=CREATOR)])
    await OutboxRelayInteractor(store).relay()
    assert store.published[0][1][0].user_id == CREATOR


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


async def test_새_리뷰는_답글_폼이_있는_프로필로_안내한다():
    """답글(갭 #53)을 달 계기가 없으면 답글 기능이 죽는다(갭 #75)."""
    record = OutboxRecord(
        id=1, event_type="review.received",
        payload={"creator_user_id": CREATOR, "creator_slug": "kim-beauty"},
    )
    store = _StubRelayStore([record])
    await OutboxRelayInteractor(store).relay()
    draft = store.published[0][1][0]
    assert draft.user_id == CREATOR
    assert draft.link == "/creators/kim-beauty"


async def test_새_지원자는_공고_브랜드에게_알린다():
    """지원 사실을 모르면 공고를 올린 의미가 없다(갭 #73)."""
    record = OutboxRecord(
        id=1, event_type="campaign.application_received",
        payload={"campaign_id": 5, "brand_user_id": BRAND,
                 "campaign_title": "신제품 릴스", "creator_name": "김뷰티"},
    )
    store = _StubRelayStore([record])
    await OutboxRelayInteractor(store).relay()
    draft = store.published[0][1][0]
    assert draft.user_id == BRAND
    assert "김뷰티" in draft.body and "신제품 릴스" in draft.body
    assert draft.link == "/campaigns/5"


async def test_인출_지급_완료는_실지급액을_알린다():
    """돈이 오가는 사건이라 공백이 특히 크다(갭 #74)."""
    record = OutboxRecord(
        id=1, event_type="withdrawal.paid",
        payload={"withdrawal_id": 3, "creator_user_id": CREATOR,
                 "amount_krw": 500_000, "payout_krw": 483_500},
    )
    store = _StubRelayStore([record])
    await OutboxRelayInteractor(store).relay()
    draft = store.published[0][1][0]
    assert draft.user_id == CREATOR
    assert "483,500원" in draft.body
    assert draft.link == "/dashboard/balance"


async def test_인출_실패는_잔액_복원을_함께_알린다():
    """복원이 조용히 일어나면 잔액 변화가 설명되지 않는다(갭 #74)."""
    record = OutboxRecord(
        id=1, event_type="withdrawal.failed",
        payload={"withdrawal_id": 3, "creator_user_id": CREATOR,
                 "amount_krw": 500_000, "payout_krw": 483_500},
    )
    store = _StubRelayStore([record])
    await OutboxRelayInteractor(store).relay()
    draft = store.published[0][1][0]
    assert draft.user_id == CREATOR
    assert "500,000원" in draft.body and "복원" in draft.body


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
