import pytest

from hub.app.dtos.package_summary_dto import PackageSummary
from payment.app.dtos.checkout_preparation_dto import CheckoutCommand
from payment.app.exceptions import NotBrandAccountError, PackageNotOrderableError
from payment.app.use_cases.checkout_preparation_interactor import CheckoutPreparationInteractor
from payment.domain.entities.payment_intent_entity import PaymentIntent, PaymentIntentStatus

BRAND, CREATOR = 100, 200
_SUMMARY = PackageSummary(package_id=10, title="릴스 1개", price_krw=300000, creator_user_id=CREATOR)


class _StubPackageSummaryPort:
    def __init__(self, summary=_SUMMARY):
        self.summary = summary

    async def get_package_summary(self, package_id):
        return self.summary if self.summary and self.summary.package_id == package_id else None


class _StubIntentRepository:
    def __init__(self):
        self.created = []

    async def create(self, pg_order_id, package_id, brand_user_id, requirements, amount_krw):
        intent = PaymentIntent(
            id=1, pg_order_id=pg_order_id, package_id=package_id, brand_user_id=brand_user_id,
            requirements=requirements, amount_krw=amount_krw, status=PaymentIntentStatus.READY,
        )
        self.created.append(intent)
        return intent

    async def find_by_pg_order_id(self, pg_order_id):
        raise NotImplementedError

    async def mark_confirmed(self, intent_id, payment_key, order_id):
        raise NotImplementedError

    async def mark_failed(self, intent_id, payment_key, reason):
        raise NotImplementedError


def _interactor(summary=_SUMMARY, intents=None):
    return CheckoutPreparationInteractor(
        intents=intents if intents is not None else _StubIntentRepository(),
        packages=_StubPackageSummaryPort(summary),
        brand_fee_percent=10,
        client_key="test_ck_dummy",
    )


def _command(package_id=10, account_type="BRAND"):
    return CheckoutCommand(
        package_id=package_id, requirements="60초 릴스", brand_user_id=BRAND,
        account_type=account_type,
    )


async def test_결제_준비는_서버가_금액을_확정한다():
    intents = _StubIntentRepository()
    result = await _interactor(intents=intents).prepare(_command())
    assert result.amount_krw == 330000  # 가격 + 브랜드 수수료 10%
    assert result.order_name == "릴스 1개"
    assert result.pg_order_id.startswith("crecity-")
    assert intents.created[0].amount_krw == 330000  # 의도에 스냅샷


async def test_크리에이터_계정이면_NotBrandAccountError():
    with pytest.raises(NotBrandAccountError):
        await _interactor().prepare(_command(account_type="CREATOR"))


async def test_없는_패키지면_PackageNotOrderableError():
    with pytest.raises(PackageNotOrderableError):
        await _interactor().prepare(_command(package_id=999))
