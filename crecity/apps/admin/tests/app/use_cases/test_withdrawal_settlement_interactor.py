import pytest

from admin.app.dtos.withdrawal_settlement_dto import SettlementDecisionCommand
from admin.app.exceptions import SettlementTargetNotFoundError
from admin.app.use_cases.withdrawal_settlement_interactor import WithdrawalSettlementInteractor
from hub.app.dtos.withdrawal_settlement_dto import AnnualPayoutSummary, WithdrawalSummary


def _summary(id=1, status="PAID"):
    return WithdrawalSummary(
        id=id,
        creator_user_id=7,
        amount_krw=100_000,
        tax_krw=3_300,
        payout_krw=96_700,
        bank_name="국민은행",
        account_number="123-456",
        account_holder="김하늘",
        status=status,
        created_at=None,
    )


class _StubPort:
    def __init__(self, found: bool = True):
        self.found = found
        self.calls: list[tuple[str, int]] = []

    async def list_pending(self):
        return [_summary(status="REQUESTED")]

    async def complete(self, withdrawal_id):
        self.calls.append(("complete", withdrawal_id))
        return _summary(status="PAID") if self.found else None

    async def fail(self, withdrawal_id):
        self.calls.append(("fail", withdrawal_id))
        return _summary(status="FAILED") if self.found else None

    async def annual_summary(self, year):
        self.calls.append(("annual_summary", year))
        return [
            AnnualPayoutSummary(
                creator_user_id=7,
                account_holder="김하늘",
                count=2,
                total_amount_krw=300_000,
                total_tax_krw=9_900,
                total_payout_krw=290_100,
            )
        ]


class _StubRecord:
    def __init__(self):
        self.notes: list[str] = []

    async def record(self, subject, note):
        self.notes.append(f"{subject}|{note}")


def _command(completed: bool):
    return SettlementDecisionCommand(
        withdrawal_id=1, completed=completed, operator_id=99, operator_email="op@crecity.kr"
    )


async def test_완료_결정은_complete를_호출하고_감사_기록을_남긴다():
    port, record = _StubPort(), _StubRecord()
    result = await WithdrawalSettlementInteractor(port, record).settle(_command(completed=True))
    assert port.calls == [("complete", 1)]
    assert result.status == "PAID"
    assert record.notes and "지급 완료" in record.notes[0]


async def test_실패_결정은_fail을_호출한다():
    port, record = _StubPort(), _StubRecord()
    result = await WithdrawalSettlementInteractor(port, record).settle(_command(completed=False))
    assert port.calls == [("fail", 1)]
    assert result.status == "FAILED"


async def test_연간_집계는_포트를_그대로_통과시킨다():
    port = _StubPort()
    summaries = await WithdrawalSettlementInteractor(port, _StubRecord()).annual_summary(2026)
    assert port.calls == [("annual_summary", 2026)]
    assert summaries[0].total_tax_krw == 9_900


async def test_대상이_없으면_SettlementTargetNotFoundError():
    interactor = WithdrawalSettlementInteractor(_StubPort(found=False), _StubRecord())
    with pytest.raises(SettlementTargetNotFoundError):
        await interactor.settle(_command(completed=True))
