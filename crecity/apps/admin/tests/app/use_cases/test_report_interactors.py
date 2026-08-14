import pytest

from admin.app.dtos.report_dto import ReportResolveCommand, ReportSubmissionCommand
from admin.app.exceptions import DuplicateReportError, ReportTargetNotFoundError
from admin.app.use_cases.report_review_interactor import ReportReviewInteractor
from admin.app.use_cases.report_submission_interactor import ReportSubmissionInteractor
from admin.domain.entities.report_entity import (
    InvalidReasonError,
    Report,
    ReportAlreadyResolvedError,
    ReportStatus,
    ReportTargetType,
)

REPORTER = 7
RESOLVER = 99


def _report(report_id: int = 1, status: ReportStatus = ReportStatus.OPEN) -> Report:
    return Report(
        id=report_id,
        reporter_user_id=REPORTER,
        target_type=ReportTargetType.PROFILE,
        target_id=3,
        reason="허위 팔로워로 의심되는 지표를 올려두었습니다.",
        status=status,
    )


class _StubReports:
    def __init__(self, existing: Report | None = None, has_open: bool = False):
        self.existing = existing
        self.has_open = has_open
        self.created: list[dict] = []
        self.resolved: list[dict] = []

    async def create(self, reporter_user_id, target_type, target_id, reason) -> Report:
        self.created.append(
            {
                "reporter_user_id": reporter_user_id,
                "target_type": target_type,
                "target_id": target_id,
                "reason": reason,
            }
        )
        return _report()

    async def find_by_id(self, report_id: int) -> Report | None:
        return self.existing

    async def exists_open_by_reporter(self, reporter_user_id, target_type, target_id) -> bool:
        return self.has_open

    async def list_open(self, limit: int) -> list[Report]:
        return [_report()] if self.existing is None else [self.existing]

    async def resolve(self, report_id: int, resolver_user_id: int, note: str):
        self.resolved.append({"id": report_id, "by": resolver_user_id, "note": note})
        from dataclasses import replace

        assert self.existing is not None
        return replace(
            self.existing,
            status=ReportStatus.RESOLVED,
            resolution_note=note,
            resolved_by_user_id=resolver_user_id,
        )


class _StubRecord:
    def __init__(self):
        self.notes: list[tuple[str, str]] = []

    async def record(self, subject: str, note: str) -> None:
        self.notes.append((subject, note))


async def test_신고를_접수하면_사유_공백을_정리해_저장한다():
    reports = _StubReports()
    result = await ReportSubmissionInteractor(reports=reports).submit(
        ReportSubmissionCommand(
            reporter_user_id=REPORTER,
            target_type="PROFILE",
            target_id=3,
            reason="  허위 팔로워로 의심되는 지표를 올려두었습니다.  ",
        )
    )
    assert reports.created[0]["reason"] == "허위 팔로워로 의심되는 지표를 올려두었습니다."
    assert reports.created[0]["target_type"] is ReportTargetType.PROFILE
    assert result.status == ReportStatus.OPEN.value


async def test_사유가_너무_짧으면_거부한다():
    with pytest.raises(InvalidReasonError):
        await ReportSubmissionInteractor(reports=_StubReports()).submit(
            ReportSubmissionCommand(
                reporter_user_id=REPORTER, target_type="PROFILE", target_id=3, reason="싫어요"
            )
        )


async def test_같은_대상에_대기_중인_신고가_있으면_중복_접수를_막는다():
    reports = _StubReports(has_open=True)
    with pytest.raises(DuplicateReportError):
        await ReportSubmissionInteractor(reports=reports).submit(
            ReportSubmissionCommand(
                reporter_user_id=REPORTER,
                target_type="PROFILE",
                target_id=3,
                reason="같은 사유로 다시 신고합니다.",
            )
        )
    assert reports.created == []


async def test_신고를_처리하면_감사_기록을_남긴다():
    reports = _StubReports(existing=_report())
    record = _StubRecord()
    result = await ReportReviewInteractor(reports=reports, record=record).resolve(
        ReportResolveCommand(report_id=1, resolver_user_id=RESOLVER, note="  경고 안내함  ")
    )
    assert result.status == ReportStatus.RESOLVED.value
    assert reports.resolved[0]["note"] == "경고 안내함"
    assert record.notes[0][0] == "report_review"
    assert "신고 #1" in record.notes[0][1]


async def test_이미_처리된_신고는_다시_처리하지_않는다():
    reports = _StubReports(existing=_report(status=ReportStatus.RESOLVED))
    with pytest.raises(ReportAlreadyResolvedError):
        await ReportReviewInteractor(reports=reports, record=_StubRecord()).resolve(
            ReportResolveCommand(report_id=1, resolver_user_id=RESOLVER, note="다시 처리")
        )
    assert reports.resolved == []


async def test_없는_신고를_처리하면_404_예외():
    with pytest.raises(ReportTargetNotFoundError):
        await ReportReviewInteractor(reports=_StubReports(), record=_StubRecord()).resolve(
            ReportResolveCommand(report_id=404, resolver_user_id=RESOLVER, note="")
        )
