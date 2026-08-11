import pytest

from order.app.dtos.withdrawal_request_dto import WithdrawalRequestCommand
from order.app.exceptions import InsufficientBalanceError, NotCreatorAccountError
from order.app.use_cases.withdrawal_request_interactor import WithdrawalRequestInteractor
from order.domain.entities.withdrawal_entity import (
    InvalidWithdrawalStateError,
    Withdrawal,
    WithdrawalStatus,
    compute_withholding_tax,
)


class _StubWithdrawals:
    def __init__(self, sufficient: bool = True):
        self.sufficient = sufficient
        self.created: list[dict] = []

    async def create_if_balance_sufficient(self, **kwargs):
        if not self.sufficient:
            return None
        self.created.append(kwargs)
        return Withdrawal(
            id=1,
            user_id=kwargs["user_id"],
            amount_krw=kwargs["amount_krw"],
            tax_krw=kwargs["tax_krw"],
            payout_krw=kwargs["payout_krw"],
            bank_name=kwargs["bank_name"],
            account_number=kwargs["account_number"],
            account_holder=kwargs["account_holder"],
            status=WithdrawalStatus.REQUESTED,
        )

    async def list_by_user(self, user_id):
        return []


def _command(amount=100_000, account_type="CREATOR"):
    return WithdrawalRequestCommand(
        user_id=7,
        account_type=account_type,
        amount_krw=amount,
        bank_name="국민은행",
        account_number="123-456",
        account_holder="김하늘",
    )


async def test_요청하면_세액과_실지급액을_계산해_차감_생성한다():
    withdrawals = _StubWithdrawals()
    interactor = WithdrawalRequestInteractor(withdrawals, tax_permille=33)
    result = await interactor.request(_command(amount=100_000))
    assert withdrawals.created[0]["tax_krw"] == 3_300  # 3.3% 내림
    assert withdrawals.created[0]["payout_krw"] == 96_700
    assert result.status == "REQUESTED"


async def test_잔액_부족이면_InsufficientBalanceError():
    interactor = WithdrawalRequestInteractor(_StubWithdrawals(sufficient=False), tax_permille=33)
    with pytest.raises(InsufficientBalanceError):
        await interactor.request(_command())


async def test_브랜드_계정은_인출_불가():
    interactor = WithdrawalRequestInteractor(_StubWithdrawals(), tax_permille=33)
    with pytest.raises(NotCreatorAccountError):
        await interactor.request(_command(account_type="BRAND"))


async def test_0원_이하_요청은_거부한다():
    interactor = WithdrawalRequestInteractor(_StubWithdrawals(), tax_permille=33)
    with pytest.raises(ValueError):
        await interactor.request(_command(amount=0))


def test_세액은_정수_원_단위_내림():
    assert compute_withholding_tax(10_000, 33) == 330
    assert compute_withholding_tax(999, 33) == 32  # 32.967 → 32


def test_처리된_인출은_재전이_불가():
    withdrawal = Withdrawal(
        id=1,
        user_id=7,
        amount_krw=1000,
        tax_krw=33,
        payout_krw=967,
        bank_name="b",
        account_number="a",
        account_holder="h",
        status=WithdrawalStatus.PAID,
    )
    with pytest.raises(InvalidWithdrawalStateError):
        withdrawal.mark_paid()
    with pytest.raises(InvalidWithdrawalStateError):
        withdrawal.mark_failed()
