from datetime import timedelta

import pytest

from hub.app.dtos.package_summary_dto import PackageSummary
from order.app.dtos.order_placement_dto import OrderPlacementCommand
from order.app.exceptions import NotBrandAccountError, PackageNotOrderableError
from order.app.use_cases.order_placement_interactor import OrderPlacementInteractor
from order.domain.entities.ledger_entry_entity import LedgerEntryType
from order.domain.entities.order_entity import OrderStatus

BRAND, CREATOR = 100, 200


class _StubPackageSummaryPort:
    def __init__(self, summary: PackageSummary | None):
        self.summary = summary

    async def get_package_summary(self, package_id):
        return self.summary if self.summary and self.summary.package_id == package_id else None


class _StubOrderRepository:
    def __init__(self):
        self.created = []  # (order, entries)

    async def create(self, order, entries, events):
        self.created.append((order, entries, events))
        from dataclasses import replace

        return replace(order, id=1)

    async def find_by_id(self, order_id):
        raise NotImplementedError

    async def save_transition(self, order, entries, events):
        raise NotImplementedError

    async def list_by_participant(self, user_id):
        raise NotImplementedError

    async def find_expired(self, now, limit):
        raise NotImplementedError


_SUMMARY = PackageSummary(package_id=10, title="릴스 1개", price_krw=300000, creator_user_id=CREATOR)


def _interactor(summary=_SUMMARY, orders=None):
    return OrderPlacementInteractor(
        orders=orders if orders is not None else _StubOrderRepository(),
        packages=_StubPackageSummaryPort(summary),
        brand_fee_percent=10,
        creator_fee_percent=10,
        accept_deadline=timedelta(hours=72),
    )


def _command(package_id=10, account_type="BRAND"):
    return OrderPlacementCommand(
        package_id=package_id,
        requirements="60초 릴스",
        brand_user_id=BRAND,
        account_type=account_type,
    )


async def test_주문하면_스냅샷과_72h_마감으로_수락_대기가_된다():
    orders = _StubOrderRepository()
    result = await _interactor(orders=orders).place(_command())

    assert result.status == OrderStatus.PENDING_ACCEPT.value
    assert result.amount_krw == 300000  # 패키지 가격 스냅샷
    assert result.brand_total_krw == 330000
    assert result.brand_fee_percent == 10  # 요율 스냅샷
    assert result.creator_user_id == CREATOR
    assert result.deadline_at is not None

    saved_order, saved_entries, saved_events = orders.created[0]
    assert saved_order.deadline_at is not None


async def test_주문_생성과_함께_에스크로_예치가_기록된다():
    orders = _StubOrderRepository()
    await _interactor(orders=orders).place(_command())
    _, entries, events = orders.created[0]
    assert len(entries) == 1
    assert entries[0].entry_type is LedgerEntryType.ESCROW_DEPOSIT
    assert entries[0].user_id == BRAND
    assert entries[0].amount_krw == 330000  # 수수료 포함 결제 총액
    assert events[0].event_type == "order.placed"  # Outbox 이벤트 동반


async def test_크리에이터_계정이면_NotBrandAccountError():
    with pytest.raises(NotBrandAccountError):
        await _interactor().place(_command(account_type="CREATOR"))


async def test_없는_패키지면_PackageNotOrderableError():
    with pytest.raises(PackageNotOrderableError):
        await _interactor().place(_command(package_id=999))


async def test_주문_불가_패키지면_PackageNotOrderableError():
    with pytest.raises(PackageNotOrderableError):
        await _interactor(summary=None).place(_command())
