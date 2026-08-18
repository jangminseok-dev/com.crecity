from order.app.dtos.monthly_report_dto import MonthlyReportQuery
from order.app.use_cases.monthly_report_interactor import MonthlyReportInteractor


class _StubLedger:
    def __init__(self, summary):
        self.summary = summary
        self.calls: list[tuple[int, int]] = []

    async def monthly_summary(self, user_id, year):
        self.calls.append((user_id, year))
        return self.summary


async def test_원장_요약을_행으로_변환한다():
    ledger = _StubLedger(
        [
            (1, "CREATOR_EARNING", 900_000, 3),
            (1, "WITHDRAWAL", 500_000, 1),
            (2, "CREATOR_EARNING", 300_000, 1),
        ]
    )
    rows = await MonthlyReportInteractor(ledger).report(MonthlyReportQuery(user_id=7, year=2026))
    assert ledger.calls == [(7, 2026)]
    assert [(r.month, r.entry_type, r.total_krw, r.count) for r in rows] == [
        (1, "CREATOR_EARNING", 900_000, 3),
        (1, "WITHDRAWAL", 500_000, 1),
        (2, "CREATOR_EARNING", 300_000, 1),
    ]


async def test_기입이_없으면_빈_목록():
    assert (
        await MonthlyReportInteractor(_StubLedger([])).report(
            MonthlyReportQuery(user_id=7, year=2020)
        )
        == []
    )
