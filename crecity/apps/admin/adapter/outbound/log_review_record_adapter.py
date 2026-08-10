from __future__ import annotations

import logging

from admin.app.ports.output.review_record_port import ReviewRecordPort

logger = logging.getLogger(__name__)


class LogReviewRecordAdapter(ReviewRecordPort):
    """심사 감사 기록을 로그로 남기는 임시 구현 — 감사 테이블 필요 시 PG 어댑터로 교체."""

    async def record(self, subject: str, note: str) -> None:
        logger.info("[admin-audit] %s | %s", subject, note)
