from admin.app.use_cases.dashboard_metrics_interactor import DashboardMetricsInteractor
from hub.app.dtos.platform_metrics_dto import AccountMetrics, OrderMetrics, ProfileMetrics


class _StubAccounts:
    def __init__(self, metrics: AccountMetrics):
        self.metrics = metrics
        self.calls = 0

    async def get_account_metrics(self) -> AccountMetrics:
        self.calls += 1
        return self.metrics


class _StubProfiles:
    def __init__(self, metrics: ProfileMetrics):
        self.metrics = metrics
        self.calls = 0

    async def get_profile_metrics(self) -> ProfileMetrics:
        self.calls += 1
        return self.metrics


class _StubOrders:
    def __init__(self, metrics: OrderMetrics):
        self.metrics = metrics
        self.calls = 0

    async def get_order_metrics(self) -> OrderMetrics:
        self.calls += 1
        return self.metrics


def _order_metrics(**overrides) -> OrderMetrics:
    defaults = dict(
        pending_accept=3,
        in_progress=5,
        in_review=2,
        completed=11,
        refunded=1,
        cancelled=0,
        gmv_krw=3_300_000,
        platform_revenue_krw=660_000,
        open_disputes=1,
        pending_withdrawals=2,
        pending_withdrawal_krw=1_450_000,
    )
    return OrderMetrics(**{**defaults, **overrides})


def _interactor(accounts=None, profiles=None, orders=None) -> DashboardMetricsInteractor:
    return DashboardMetricsInteractor(
        accounts=accounts or _StubAccounts(AccountMetrics(0, 0, 0)),
        profiles=profiles or _StubProfiles(ProfileMetrics(0, 0, 0)),
        orders=orders or _StubOrders(_order_metrics()),
    )


async def test_세_스포크_집계를_한_결과로_합친다():
    accounts = _StubAccounts(AccountMetrics(total_users=42, creator_users=30, brand_users=12))
    profiles = _StubProfiles(ProfileMetrics(pending_review=4, approved=25, rejected=1))
    orders = _StubOrders(_order_metrics())
    result = await _interactor(accounts, profiles, orders).get_metrics()

    assert (result.total_users, result.creator_users, result.brand_users) == (42, 30, 12)
    assert (result.pending_review, result.approved_profiles, result.rejected_profiles) == (4, 25, 1)
    assert result.gmv_krw == 3_300_000
    assert result.platform_revenue_krw == 660_000
    assert result.open_disputes == 1
    assert (result.pending_withdrawals, result.pending_withdrawal_krw) == (2, 1_450_000)


async def test_포트마다_한_번씩만_조회한다():
    accounts = _StubAccounts(AccountMetrics(1, 1, 0))
    profiles = _StubProfiles(ProfileMetrics(0, 1, 0))
    orders = _StubOrders(_order_metrics())
    await _interactor(accounts, profiles, orders).get_metrics()
    assert (accounts.calls, profiles.calls, orders.calls) == (1, 1, 1)


async def test_주문_상태별_건수를_그대로_전달한다():
    orders = _StubOrders(_order_metrics(pending_accept=7, in_review=0, cancelled=3))
    result = await _interactor(orders=orders).get_metrics()
    assert result.pending_accept == 7
    assert result.in_review == 0
    assert result.cancelled == 3
