from __future__ import annotations

import logging

from review.app.ports.output.appraiser_record_port import AppraiserRecordPort

logger = logging.getLogger(__name__)


class LogAppraiserRecordAdapter(AppraiserRecordPort):
    """활동 기록을 로그로 남기는 임시 구현. 영속 기록이 필요해지면 PG 어댑터로 교체."""

    async def record(self, subject: str, note: str) -> None:
        logger.info("[appraiser-record] %s | %s", subject, note)
