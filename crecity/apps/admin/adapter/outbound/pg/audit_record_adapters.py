from __future__ import annotations

import logging

from admin.app.ports.output.audit_log_repository import AuditLogRepository
from admin.app.ports.output.dispute_record_port import DisputeRecordPort
from admin.app.ports.output.report_record_port import ReportRecordPort
from admin.app.ports.output.review_record_port import ReviewRecordPort
from admin.app.ports.output.settlement_record_port import SettlementRecordPort
from admin.app.ports.output.steward_record_port import StewardRecordPort

logger = logging.getLogger(__name__)


class PgAuditRecordAdapter(
    ReviewRecordPort,
    SettlementRecordPort,
    StewardRecordPort,
    DisputeRecordPort,
    ReportRecordPort,
):
    """다섯 감사 기록 포트의 공용 PG 구현(갭 #36) — 같은 테이블에 subject로 구분해 쌓는다.

    기록 실패가 본래 작업(심사·인출 처리·분쟁 판정·신고 처리)을 되돌리지는 않는다 — 로그로 남기고 통과시킨다.
    """

    def __init__(self, repository: AuditLogRepository) -> None:
        self._repository = repository

    async def record(self, subject: str, note: str) -> None:
        try:
            await self._repository.append(subject, note)
        except Exception:  # noqa: BLE001 — 감사 기록 실패가 운영 동작을 막지 않게
            logger.exception("[admin-audit] 기록 실패: %s | %s", subject, note)
