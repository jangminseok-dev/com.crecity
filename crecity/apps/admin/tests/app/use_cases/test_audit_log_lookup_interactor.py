from datetime import datetime, timezone

from admin.adapter.outbound.pg.audit_record_adapters import PgAuditRecordAdapter
from admin.app.ports.output.audit_log_repository import AuditLogEntry
from admin.app.use_cases.audit_log_lookup_interactor import AuditLogLookupInteractor

_NOW = datetime(2026, 8, 11, 12, 0, tzinfo=timezone.utc)


class _StubAuditLogRepository:
    def __init__(self, entries=None, fail=False):
        self.entries = entries or []
        self.appended: list[tuple[str, str]] = []
        self.fail = fail

    async def append(self, subject, note):
        if self.fail:
            raise RuntimeError("DB 장애")
        self.appended.append((subject, note))

    async def list_recent(self, limit):
        return self.entries[:limit]


def _entry(entry_id=1, subject="profile_review", note="프로필 1 승인"):
    return AuditLogEntry(id=entry_id, subject=subject, note=note, created_at=_NOW)


async def test_최근_기록을_최신순_그대로_돌려준다():
    repository = _StubAuditLogRepository([_entry(2), _entry(1)])
    results = await AuditLogLookupInteractor(repository).list_recent()
    assert [r.id for r in results] == [2, 1]
    assert results[0].subject == "profile_review"


async def test_기록이_없으면_빈_목록이다():
    results = await AuditLogLookupInteractor(_StubAuditLogRepository()).list_recent()
    assert results == []


async def test_감사_기록은_저장소에_append된다():
    repository = _StubAuditLogRepository()
    await PgAuditRecordAdapter(repository).record("withdrawal_settlement", "인출 3 지급완료")
    assert repository.appended == [("withdrawal_settlement", "인출 3 지급완료")]


async def test_기록_실패해도_운영_동작을_막지_않는다():
    # 감사 기록은 부수효과 — DB가 흔들려도 심사·인출 처리 자체는 통과해야 한다
    repository = _StubAuditLogRepository(fail=True)
    await PgAuditRecordAdapter(repository).record("profile_review", "프로필 9 반려")
    assert repository.appended == []
