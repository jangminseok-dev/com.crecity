from creator.app.use_cases.market_rates_interactor import MarketRatesInteractor
from creator.domain.value_objects.market_rate import MarketRateEntry, summarize_market_rates
from hub.app.dtos.completed_order_price_dto import PackageOrderAmount


class _StubPackages:
    def __init__(self, classification=None):
        self.classification = classification or {}
        self.calls: list[list[int]] = []

    async def classify_by_package_ids(self, package_ids):
        self.calls.append(sorted(package_ids))
        return {pid: c for pid, c in self.classification.items() if pid in package_ids}


class _StubPrices:
    def __init__(self, amounts):
        self.amounts = amounts

    async def list_completed_package_amounts(self):
        return self.amounts


def _interactor(prices, packages=None, min_samples=3):
    return MarketRatesInteractor(
        packages=packages or _StubPackages(),
        completed_prices=_StubPrices(prices),
        min_samples=min_samples,
    )


# --- 도메인 집계 함수 ---


def test_중앙값과_사분위_범위를_낸다():
    entries = [
        MarketRateEntry("뷰티", "INSTAGRAM", amount)
        for amount in (100_000, 200_000, 300_000, 400_000, 500_000)
    ]
    [rate] = summarize_market_rates(entries, min_samples=3)
    assert rate.sample_count == 5
    assert rate.median_krw == 300_000
    assert rate.p25_krw == 200_000
    assert rate.p75_krw == 400_000


def test_표본_미달_조합은_내지_않는다():
    entries = [
        MarketRateEntry("뷰티", "INSTAGRAM", 100_000),
        MarketRateEntry("뷰티", "INSTAGRAM", 200_000),
        MarketRateEntry("뷰티", "INSTAGRAM", 300_000),
        MarketRateEntry("테크", "YOUTUBE", 900_000),  # 1건 — 미달
    ]
    rates = summarize_market_rates(entries, min_samples=3)
    assert [(r.category, r.platform) for r in rates] == [("뷰티", "INSTAGRAM")]


def test_카테고리_플랫폼_순으로_정렬한다():
    entries = [
        MarketRateEntry("테크", "YOUTUBE", 1),
        MarketRateEntry("뷰티", "YOUTUBE", 1),
        MarketRateEntry("뷰티", "INSTAGRAM", 1),
    ]
    rates = summarize_market_rates(entries, min_samples=1)
    assert [(r.category, r.platform) for r in rates] == [
        ("뷰티", "INSTAGRAM"),
        ("뷰티", "YOUTUBE"),
        ("테크", "YOUTUBE"),
    ]


# --- 인터랙터 ---


async def test_분류를_결합해_시세를_낸다():
    packages = _StubPackages(
        {
            1: ("뷰티", "INSTAGRAM"),
            2: ("뷰티", "INSTAGRAM"),
        }
    )
    prices = [
        PackageOrderAmount(package_id=1, amount_krw=200_000),
        PackageOrderAmount(package_id=1, amount_krw=300_000),
        PackageOrderAmount(package_id=2, amount_krw=400_000),
    ]
    [rate] = await _interactor(prices, packages).list_market_rates()
    assert (rate.category, rate.platform) == ("뷰티", "INSTAGRAM")
    assert rate.sample_count == 3
    assert rate.median_krw == 300_000
    # 같은 패키지가 여러 번 거래돼도 분류 조회는 중복 없이 한 번에
    assert packages.calls == [[1, 2]]


async def test_분류할_수_없는_거래는_제외한다():
    packages = _StubPackages({1: ("뷰티", "INSTAGRAM")})
    prices = [
        PackageOrderAmount(package_id=1, amount_krw=100_000),
        PackageOrderAmount(package_id=1, amount_krw=200_000),
        PackageOrderAmount(package_id=1, amount_krw=300_000),
        PackageOrderAmount(package_id=99, amount_krw=900_000),  # 삭제된 패키지
    ]
    [rate] = await _interactor(prices, packages).list_market_rates()
    assert rate.sample_count == 3


async def test_거래가_없으면_빈_목록():
    assert await _interactor([]).list_market_rates() == []
