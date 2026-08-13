from datetime import datetime, timedelta, timezone

import pytest

from order.app.dtos.deliverable_submission_dto import (
    DeliverableListQuery,
    SubmitDeliverableFileCommand,
    SubmitDeliverableLinkCommand,
)
from order.app.exceptions import NotOrderParticipantError, OrderNotFoundError
from order.app.use_cases.deliverable_submission_interactor import (
    DeliverableSubmissionInteractor,
)
from order.domain.entities.deliverable_entity import Deliverable, DeliverableKind
from order.domain.entities.order_entity import (
    InvalidOrderTransitionError,
    NotOrderActorError,
    Order,
    OrderStatus,
)

_NOW = datetime(2026, 8, 11, 12, 0, tzinfo=timezone.utc)
BRAND, CREATOR = 100, 200


class _StubOrderRepository:
    def __init__(self, order: Order | None):
        self.order = order

    async def create(self, order, entries, events):
        raise NotImplementedError

    async def find_by_id(self, order_id):
        return self.order if self.order and self.order.id == order_id else None

    async def save_transition(self, order, entries, events):
        raise NotImplementedError

    async def list_by_participant(self, user_id):
        raise NotImplementedError

    async def find_expired(self, now, limit):
        raise NotImplementedError


class _StubDeliverableRepository:
    def __init__(self):
        self.items: list[Deliverable] = []

    async def add(self, order_id, kind, file_name, original_name, url, caption):
        deliverable = Deliverable(
            id=len(self.items) + 1,
            order_id=order_id,
            kind=kind,
            file_name=file_name,
            original_name=original_name,
            url=url,
            caption=caption,
            created_at=_NOW,
        )
        self.items.append(deliverable)
        return deliverable

    async def list_by_order(self, order_id):
        return [d for d in self.items if d.order_id == order_id]

    async def count_by_order(self, order_id):
        return len([d for d in self.items if d.order_id == order_id])


class _StubStorage:
    def __init__(self):
        self.saved = []

    def save(self, content, extension):
        self.saved.append((content, extension))
        return f"stub{len(self.saved)}.{extension}"


def _order(status=OrderStatus.IN_PROGRESS):
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
        status=status,
        deadline_at=None if status is OrderStatus.IN_PROGRESS else _NOW + timedelta(hours=72),
    )


def _interactor(order):
    deliverables = _StubDeliverableRepository()
    storage = _StubStorage()
    interactor = DeliverableSubmissionInteractor(
        orders=_StubOrderRepository(order), deliverables=deliverables, storage=storage
    )
    return interactor, deliverables, storage


def _file_command(actor=CREATOR, content_type="image/png", original_name="결과물.png"):
    return SubmitDeliverableFileCommand(
        order_id=1,
        actor_user_id=actor,
        content=b"binary",
        content_type=content_type,
        original_name=original_name,
    )


async def test_파일을_등록하면_저장되고_기록된다():
    interactor, deliverables, storage = _interactor(_order())
    result = await interactor.submit_file(_file_command())
    assert storage.saved == [(b"binary", "png")]
    assert result.kind == DeliverableKind.FILE.value
    assert result.file_name == "stub1.png"
    assert result.original_name == "결과물.png"
    assert len(deliverables.items) == 1


async def test_링크를_등록하면_기록된다():
    interactor, deliverables, _ = _interactor(_order())
    result = await interactor.submit_link(
        SubmitDeliverableLinkCommand(
            order_id=1, actor_user_id=CREATOR, url="https://instagram.com/p/abc"
        )
    )
    assert result.kind == DeliverableKind.LINK.value
    assert result.url == "https://instagram.com/p/abc"
    assert len(deliverables.items) == 1


async def test_본문에_광고_표기가_있으면_검수를_통과한다():
    interactor, _, _ = _interactor(_order())
    result = await interactor.submit_link(
        SubmitDeliverableLinkCommand(
            order_id=1,
            actor_user_id=CREATOR,
            url="https://instagram.com/p/abc",
            caption="신상 립밤 써봤어요 #광고",
        )
    )
    assert result.caption == "신상 립밤 써봤어요 #광고"
    assert result.ad_disclosure_ok is True


async def test_본문에_광고_표기가_없으면_미확인이다():
    interactor, _, _ = _interactor(_order())
    result = await interactor.submit_link(
        SubmitDeliverableLinkCommand(
            order_id=1, actor_user_id=CREATOR, url="https://instagram.com/p/abc", caption="써봤어요"
        )
    )
    assert result.ad_disclosure_ok is False


async def test_파일_납품물은_광고_표기_검수_대상이_아니다():
    interactor, _, _ = _interactor(_order())
    result = await interactor.submit_file(_file_command())
    assert result.ad_disclosure_ok is None


async def test_본문이_너무_길면_ValueError():
    interactor, _, _ = _interactor(_order())
    with pytest.raises(ValueError):
        await interactor.submit_link(
            SubmitDeliverableLinkCommand(
                order_id=1, actor_user_id=CREATOR, url="https://a.b", caption="가" * 3001
            )
        )


async def test_브랜드가_등록하면_NotOrderActorError():
    interactor, _, storage = _interactor(_order())
    with pytest.raises(NotOrderActorError):
        await interactor.submit_file(_file_command(actor=BRAND))
    assert storage.saved == []  # 검증 실패 시 파일이 저장되지 않는다


async def test_작업중이_아니면_InvalidOrderTransitionError():
    interactor, _, _ = _interactor(_order(OrderStatus.IN_REVIEW))
    with pytest.raises(InvalidOrderTransitionError):
        await interactor.submit_link(
            SubmitDeliverableLinkCommand(order_id=1, actor_user_id=CREATOR, url="https://a.b")
        )


async def test_지원하지_않는_파일_형식이면_ValueError():
    interactor, _, _ = _interactor(_order())
    with pytest.raises(ValueError):
        await interactor.submit_file(_file_command(content_type="text/plain"))


async def test_http가_아닌_링크면_ValueError():
    interactor, _, _ = _interactor(_order())
    with pytest.raises(ValueError):
        await interactor.submit_link(
            SubmitDeliverableLinkCommand(order_id=1, actor_user_id=CREATOR, url="ftp://a.b")
        )


async def test_목록은_당사자만_조회할_수_있다():
    interactor, _, _ = _interactor(_order())
    await interactor.submit_link(
        SubmitDeliverableLinkCommand(order_id=1, actor_user_id=CREATOR, url="https://a.b")
    )
    results = await interactor.list_deliverables(
        DeliverableListQuery(order_id=1, requester_user_id=BRAND)
    )
    assert len(results) == 1
    with pytest.raises(NotOrderParticipantError):
        await interactor.list_deliverables(
            DeliverableListQuery(order_id=1, requester_user_id=999)
        )


async def test_없는_주문이면_OrderNotFoundError():
    interactor, _, _ = _interactor(None)
    with pytest.raises(OrderNotFoundError):
        await interactor.submit_file(_file_command())
