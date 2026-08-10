from order.app.dtos.balance_lookup_dto import BalanceQuery
from order.app.use_cases.balance_lookup_interactor import BalanceLookupInteractor


class _StubLedgerRepository:
    def __init__(self, balances: dict[int, int]):
        self.balances = balances

    async def balance_krw(self, user_id):
        return self.balances.get(user_id, 0)


async def test_원장_합산_잔액을_돌려준다():
    interactor = BalanceLookupInteractor(_StubLedgerRepository({200: 270000}))
    result = await interactor.get_balance(BalanceQuery(user_id=200))
    assert result.balance_krw == 270000


async def test_기입이_없으면_잔액은_0이다():
    interactor = BalanceLookupInteractor(_StubLedgerRepository({}))
    result = await interactor.get_balance(BalanceQuery(user_id=999))
    assert result.balance_krw == 0
