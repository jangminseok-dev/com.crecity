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


def _intent(status=PaymentIntentStatus.READY, amount_krw=330000, credit_applied_krw=0):
    return PaymentIntent(
        id=1, pg_order_id="crecity-abc", package_id=10, brand_user_id=BRAND,
        requirements="60초 릴스", amount_krw=amount_krw, status=status,
        credit_applied_krw=credit_applied_krw,
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
        self.credits = []  # 전달된 credit_used_krw

    async def place_paid_order(
        self, package_id, requirements, brand_user_id, expected_brand_total_krw,
        credit_used_krw=0,
    ):
        self.calls.append((package_id, expected_brand_total_krw))
        self.credits.append(credit_used_krw)
        return self.placed


def _command(amount_krw=330000, requester=BRAND, payment_key="pay-key"):
    return ConfirmCommand(
        payment_key=payment_key, pg_order_id="crecity-abc",
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


# ── 크레딧 결제 (갭 #5) ───────────────────────────────────────────


async def test_부분_크레딧은_PG에_차액만_청구하고_크레딧을_전달한다():
    intents = _StubIntentRepository(_intent(credit_applied_krw=100000))
    gateway = _StubGateway()
    orders = _StubOrderPlacementPort(PlacedOrder(id=7, brand_total_krw=330000))
    result = await PaymentConfirmationInteractor(intents, gateway, orders).confirm(
        _command(amount_krw=230000)  # 리다이렉트 amount = PG 청구액
    )
    assert result.order_id == 7
    assert gateway.confirms == [("pay-key", "crecity-abc", 230000)]
    assert orders.calls == [(10, 330000)]  # 주문 금액 대조는 총액 기준
    assert orders.credits == [100000]


async def test_전액_크레딧은_PG를_거치지_않고_주문을_생성한다():
    intents = _StubIntentRepository(_intent(credit_applied_krw=330000))
    gateway = _StubGateway()
    orders = _StubOrderPlacementPort(PlacedOrder(id=7, brand_total_krw=330000))
    result = await PaymentConfirmationInteractor(intents, gateway, orders).confirm(
        _command(amount_krw=0, payment_key="")
    )
    assert result.order_id == 7
    assert gateway.confirms == []  # PG 호출 없음
    assert orders.credits == [330000]
    assert intents.confirmed == [(1, "", 7)]


async def test_전액_크레딧_주문_생성_실패는_PG_취소_없이_FAILED_기록():
    intents = _StubIntentRepository(_intent(credit_applied_krw=330000))
    gateway = _StubGateway()
    interactor = PaymentConfirmationInteractor(intents, gateway, _StubOrderPlacementPort(None))
    with pytest.raises(PaymentConfirmError):
        await interactor.confirm(_command(amount_krw=0, payment_key=""))
    assert gateway.cancels == []  # 되돌릴 PG 결제가 없다
    assert "보정 불필요" in intents.failed[0][2]


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


# ── 커스텀 오퍼 결제 승인 ─────────────────────────────────────────


class _StubCustomOfferPortForConfirm:
    def __init__(self):
        self.paid = []  # (offer_id, order_id)

    async def get_payable_offer(self, offer_id):
        raise NotImplementedError

    async def mark_paid(self, offer_id, order_id):
        self.paid.append((offer_id, order_id))


class _StubOrderPlacementPortWithCustom(_StubOrderPlacementPort):
    def __init__(self, placed):
        super().__init__(placed)
        self.custom_calls = []

    async def place_paid_custom_order(
        self, offer_id, requirements, brand_user_id, expected_brand_total_krw,
        credit_used_krw=0,
    ):
        self.custom_calls.append((offer_id, expected_brand_total_krw))
        return self.placed


async def test_오퍼_결제는_커스텀_주문으로_생성되고_오퍼가_PAID_처리된다():
    intent = PaymentIntent(
        id=1, pg_order_id="crecity-abc", package_id=None, brand_user_id=BRAND,
        requirements="협의 내용대로", amount_krw=495000,
        status=PaymentIntentStatus.READY, offer_id=5,
    )
    intents = _StubIntentRepository(intent)
    orders = _StubOrderPlacementPortWithCustom(PlacedOrder(id=9, brand_total_krw=495000))
    offers = _StubCustomOfferPortForConfirm()
    result = await PaymentConfirmationInteractor(
        intents, _StubGateway(), orders, offers=offers
    ).confirm(_command(amount_krw=495000))

    assert result.order_id == 9
    assert orders.custom_calls == [(5, 495000)]
    assert orders.calls == []  # 패키지 경로는 타지 않는다
    assert offers.paid == [(5, 9)]


# ── 장바구니 결제 승인 (갭 #8) ────────────────────────────────────


class _StubOrderPlacementPortWithCart(_StubOrderPlacementPort):
    def __init__(self, placed_list):
        super().__init__(None)
        self.placed_list = placed_list
        self.cart_calls = []

    async def place_paid_cart_orders(
        self, package_ids, requirements, brand_user_id, expected_brand_total_krw,
        credit_used_krw=0,
    ):
        self.cart_calls.append((tuple(package_ids), expected_brand_total_krw))
        return self.placed_list


async def test_장바구니_결제는_주문_전체_id를_돌려준다():
    intent = PaymentIntent(
        id=1, pg_order_id="crecity-abc", package_id=None, brand_user_id=BRAND,
        requirements="공통 브리프", amount_krw=550000,
        status=PaymentIntentStatus.READY, cart_package_ids=(10, 11),
    )
    intents = _StubIntentRepository(intent)
    orders = _StubOrderPlacementPortWithCart(
        [PlacedOrder(id=7, brand_total_krw=330000), PlacedOrder(id=8, brand_total_krw=220000)]
    )
    result = await PaymentConfirmationInteractor(intents, _StubGateway(), orders).confirm(
        _command(amount_krw=550000)
    )
    assert result.order_id == 7
    assert result.order_ids == (7, 8)
    assert orders.cart_calls == [((10, 11), 550000)]
    assert intents.confirmed == [(1, "pay-key", 7)]


async def test_장바구니_주문_생성_실패면_결제를_취소_보정한다():
    intent = PaymentIntent(
        id=1, pg_order_id="crecity-abc", package_id=None, brand_user_id=BRAND,
        requirements="공통 브리프", amount_krw=550000,
        status=PaymentIntentStatus.READY, cart_package_ids=(10, 11),
    )
    intents = _StubIntentRepository(intent)
    gateway = _StubGateway()
    orders = _StubOrderPlacementPortWithCart(None)
    with pytest.raises(PaymentConfirmError):
        await PaymentConfirmationInteractor(intents, gateway, orders).confirm(
            _command(amount_krw=550000)
        )
    assert len(gateway.cancels) == 1


# ── 캠페인 지원 수락 결제 승인 (갭 #7) ────────────────────────────


class _StubCampaignApplicationPortForConfirm:
    def __init__(self):
        self.paid = []  # (application_id, order_id)

    async def get_payable_application(self, application_id):
        raise NotImplementedError

    async def mark_paid(self, application_id, order_id):
        self.paid.append((application_id, order_id))


class _StubOrderPlacementPortWithApplication(_StubOrderPlacementPort):
    def __init__(self, placed):
        super().__init__(placed)
        self.application_calls = []

    async def place_paid_application_order(
        self, application_id, requirements, brand_user_id, expected_brand_total_krw,
        credit_used_krw=0,
    ):
        self.application_calls.append((application_id, expected_brand_total_krw))
        return self.placed


async def test_지원_수락_결제는_지원_주문으로_생성되고_지원이_PAID_처리된다():
    intent = PaymentIntent(
        id=1, pg_order_id="crecity-abc", package_id=None, brand_user_id=BRAND,
        requirements="공고 내용대로", amount_krw=550000,
        status=PaymentIntentStatus.READY, application_id=3,
    )
    intents = _StubIntentRepository(intent)
    orders = _StubOrderPlacementPortWithApplication(PlacedOrder(id=11, brand_total_krw=550000))
    applications = _StubCampaignApplicationPortForConfirm()
    result = await PaymentConfirmationInteractor(
        intents, _StubGateway(), orders, applications=applications
    ).confirm(_command(amount_krw=550000))

    assert result.order_id == 11
    assert orders.application_calls == [(3, 550000)]
    assert orders.calls == []  # 패키지 경로는 타지 않는다
    assert applications.paid == [(3, 11)]
