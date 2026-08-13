import pytest

from admin.app.dtos.dispute_resolution_dto import DisputeDecisionCommand
from admin.app.exceptions import DisputeTargetNotFoundError
from admin.app.use_cases.dispute_resolution_interactor import DisputeResolutionInteractor
from hub.app.dtos.dispute_resolution_dto import DisputeSummary


def _summary(resolution="REFUND", status="RESOLVED"):
    return DisputeSummary(
        id=1,
        order_id=42,
        package_title="릴스 1개",
        brand_user_id=100,
        creator_user_id=200,
        amount_krw=300_000,
        brand_total_krw=330_000,
        order_status="CANCELLED",
        raised_by_user_id=100,
        reason="요구사항과 다른 결과물이 제출되었습니다.",
        status=status,
        resolution=resolution,
        created_at=None,
    )


class _StubPort:
    def __init__(self, found: bool = True):
        self.found = found
        self.calls: list[tuple[int, str, int]] = []

    async def list_open(self):
        return [_summary(resolution=None, status="OPEN")]

    async def resolve(self, dispute_id, resolution, operator_user_id):
        self.calls.append((dispute_id, resolution, operator_user_id))
        return _summary(resolution=resolution) if self.found else None


class _StubRecord:
    def __init__(self):
        self.notes: list[str] = []

    async def record(self, subject, note):
        self.notes.append(f"{subject}|{note}")


def _command(resolution: str):
    return DisputeDecisionCommand(
        dispute_id=1, resolution=resolution, operator_id=99, operator_email="op@crecity.kr"
    )


async def test_환불_판정은_포트에_전달되고_감사_기록을_남긴다():
    port, record = _StubPort(), _StubRecord()
    result = await DisputeResolutionInteractor(port, record).resolve(_command("REFUND"))
    assert port.calls == [(1, "REFUND", 99)]
    assert result.resolution == "REFUND"
    assert record.notes and "브랜드 전액 환불" in record.notes[0]


async def test_지급_판정도_같은_경로로_처리된다():
    port, record = _StubPort(), _StubRecord()
    result = await DisputeResolutionInteractor(port, record).resolve(_command("RELEASE"))
    assert port.calls == [(1, "RELEASE", 99)]
    assert result.resolution == "RELEASE"
    assert "크리에이터 전액 지급" in record.notes[0]


async def test_기각_판정은_기각으로_기록된다():
    port, record = _StubPort(), _StubRecord()
    await DisputeResolutionInteractor(port, record).resolve(_command("DISMISS"))
    assert "기각" in record.notes[0]


async def test_대상이_없으면_DisputeTargetNotFoundError():
    interactor = DisputeResolutionInteractor(_StubPort(found=False), _StubRecord())
    with pytest.raises(DisputeTargetNotFoundError):
        await interactor.resolve(_command("REFUND"))


async def test_대기_목록은_포트를_그대로_통과시킨다():
    results = await DisputeResolutionInteractor(_StubPort(), _StubRecord()).list_open()
    assert len(results) == 1 and results[0].status == "OPEN"
