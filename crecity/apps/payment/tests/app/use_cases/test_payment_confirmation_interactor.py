import pytest

from hub.app.dtos.placed_order_dto import PlacedOrder
from payment.app.dtos.payment_confirmation_dto import ConfirmCommand
from payment.app.exceptions import (
    NotPaymentOwnerError,
    PaymentAlreadyProcessedError,
    PaymentAmountMismatchError,
    PaymentConfirmError,
    PaymentIntentNotFoundError,
)
from payment.app.use_cases.payment_confirmation_interactor import PaymentConfirmationInteractor
from payment.domain.entities.payment_intent_entity import PaymentIntent, PaymentIntentStatus

BRAND = 100


def _intent(status=PaymentIntentStatus.READY, amount_krw=330000):
    return PaymentIntent(
        id=1, pg_order_id="crecity-abc", package_id=10, brand_user_id=BRAND,
        requirements="60초 릴스", amount_krw=amount_krw, status=status,
    )


class _StubIntentRepository:
    def __init__(self, intent: PaymentIntent | None):
        self.intent = intent
        self.confirmed = []
        self.failed = []  # (intent_id, payment_key, reason)

    async def create(self, **kwargs):
        raise NotImplementedError

    async def find_by_pg_order_id(self, pg_order_id):
        return self.intent if self.intent and self.intent.pg_order_id == pg_order_id else None

    async def mark_confirmed(self, intent_id, payment_key, order_id):
        self.confirmed.append((intent_id, payment_key, order_id))

    async def mark_failed(self, intent_id, payment_key, reason):
        self.failed.append((intent_id, payment_key, reason))


class _StubGateway:
    def __init__(self, confirm_ok=True, cancel_ok=True):
        self.confirm_ok = confirm_ok
        self.cancel_ok = cancel_ok
        self.confirms = []
        self.cancels = []

    async def confirm(self, payment_key, pg_order_id, amount_krw):
        self.confirms.append((payment_key, pg_order_id, amount_krw))
        if not self.confirm_ok:
            raise PaymentConfirmError("카드 한도 초과")

    async def cancel(self, payment_key, reason):
        self.cancels.append((payment_key, reason))
        if not self.cancel_ok:
            raise PaymentConfirmError("취소 실패")


class _StubOrderPlacementPort:
    def __init__(self, placed: PlacedOrder | None):
        self.placed = placed
        self.calls = []

    async def place_paid_order(self, package_id, requirements, brand_user_id, expected_brand_total_krw):
        self.calls.append((package_id, expected_brand_total_krw))
        return self.placed


def _command(amount_krw=330000, requester=BRAND):
    return ConfirmCommand(
        payment_key="pay-key", pg_order_id="crecity-abc",
        amount_krw=amount_krw, requester_user_id=requester,
    )


async def test_승인_성공하면_주문이_생성되고_CONFIRMED로_기록된다():
    intents = _StubIntentRepository(_intent())
    gateway = _StubGateway()
    orders = _StubOrderPlacementPort(PlacedOrder(id=7, brand_total_krw=330000))
    result = await PaymentConfirmationInteractor(intents, gateway, orders).confirm(_command())

    assert result.order_id == 7
    assert gateway.confirms == [("pay-key", "crecity-abc", 330000)]
    assert orders.calls == [(10, 330000)]  # 결제 금액을 기대값으로 전달
    assert intents.confirmed == [(1, "pay-key", 7)]


async def test_금액이_다르면_승인_없이_거부하고_FAILED_기록():
    intents = _StubIntentRepository(_intent())
    gateway = _StubGateway()
    interactor = PaymentConfirmationInteractor(intents, gateway, _StubOrderPlacementPort(None))
    with pytest.raises(PaymentAmountMismatchError):
        await interactor.confirm(_command(amount_krw=999999))
    assert gateway.confirms == []  # PG 호출 자체를 안 한다
    assert len(intents.failed) == 1


async def test_PG_승인_실패면_FAILED_기록_후_전파():
    intents = _StubIntentRepository(_intent())
    interactor = PaymentConfirmationInteractor(
        intents, _StubGateway(confirm_ok=False), _StubOrderPlacementPort(None)
    )
    with pytest.raises(PaymentConfirmError):
        await interactor.confirm(_command())
    assert "승인 실패" in intents.failed[0][2]


async def test_주문_생성_실패면_결제를_취소_보정한다():
    intents = _StubIntentRepository(_intent())
    gateway = _StubGateway()
    interactor = PaymentConfirmationInteractor(intents, gateway, _StubOrderPlacementPort(None))
    with pytest.raises(PaymentConfirmError):
        await interactor.confirm(_command())
    assert len(gateway.cancels) == 1  # §3 보정: PG 취소
    assert "취소 보정 완료" in intents.failed[0][2]


async def test_이미_처리된_결제는_PaymentAlreadyProcessedError():
    intents = _StubIntentRepository(_intent(status=PaymentIntentStatus.CONFIRMED))
    interactor = PaymentConfirmationInteractor(intents, _StubGateway(), _StubOrderPlacementPort(None))
    with pytest.raises(PaymentAlreadyProcessedError):
        await interactor.confirm(_command())


async def test_남의_결제_승인_시도는_NotPaymentOwnerError():
    interactor = PaymentConfirmationInteractor(
        _StubIntentRepository(_intent()), _StubGateway(), _StubOrderPlacementPort(None)
    )
    with pytest.raises(NotPaymentOwnerError):
        await interactor.confirm(_command(requester=999))


async def test_없는_결제면_PaymentIntentNotFoundError():
    interactor = PaymentConfirmationInteractor(
        _StubIntentRepository(None), _StubGateway(), _StubOrderPlacementPort(None)
    )
    with pytest.raises(PaymentIntentNotFoundError):
        await interactor.confirm(_command())
