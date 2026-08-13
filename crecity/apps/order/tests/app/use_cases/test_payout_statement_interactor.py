from datetime import datetime, timezone

from order.app.dtos.payout_statement_dto import StatementQuery
from order.app.use_cases.payout_statement_interactor import PayoutStatementInteractor
from order.domain.entities.withdrawal_entity import Withdrawal, WithdrawalStatus

CREATOR = 7


def _paid(id: int, amount: int, tax: int, year: int = 2026):
    return Withdrawal(
        id=id,
        user_id=CREATOR,
        amount_krw=amount,
        tax_krw=tax,
        payout_krw=amount - tax,
        bank_name="국민은행",
        account_number="123-456",
        account_holder="김하늘",
        status=WithdrawalStatus.PAID,
        settled_at=datetime(year, 5, 1, tzinfo=timezone.utc),
    )


class _StubWithdrawalRepository:
    def __init__(self, items: list[Withdrawal]):
        self.items = items
        self.queries: list[tuple[int, int | None]] = []

    async def create_if_balance_sufficient(self, **kwargs):
        raise NotImplementedError

    async def find_by_id(self, withdrawal_id):
        raise NotImplementedError

    async def list_by_user(self, user_id):
        raise NotImplementedError

    async def list_by_status(self, status):
        raise NotImplementedError

    async def list_paid_in_year(self, year, user_id=None):
        self.queries.append((year, user_id))
        return self.items

    async def save_settlement(self, withdrawal, entries):
        raise NotImplementedError


async def test_연간_지급명세는_합계와_건별_내역을_함께_준다():
    repository = _StubWithdrawalRepository(
        [_paid(1, 100_000, 3_300), _paid(2, 200_000, 6_600)]
    )
    result = await PayoutStatementInteractor(repository).statement(
        StatementQuery(user_id=CREATOR, year=2026)
    )
    assert repository.queries == [(2026, CREATOR)]  # 본인 몫만 조회한다
    assert result.count == 2
    assert result.total_amount_krw == 300_000
    assert result.total_tax_krw == 9_900
    assert result.total_payout_krw == 290_100
    assert [item.withdrawal_id for item in result.items] == [1, 2]


async def test_지급_내역이_없으면_0원_명세를_준다():
    result = await PayoutStatementInteractor(_StubWithdrawalRepository([])).statement(
        StatementQuery(user_id=CREATOR, year=2025)
    )
    assert (result.count, result.total_amount_krw, result.total_payout_krw) == (0, 0, 0)
    assert result.items == []
    assert result.year == 2025
