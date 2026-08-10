from __future__ import annotations

import logging

from campaign.app.ports.output.herald_record_port import HeraldRecordPort

logger = logging.getLogger(__name__)


class LogHeraldRecordAdapter(HeraldRecordPort):
    """활동 기록을 로그로 남기는 임시 구현. 영속 기록이 필요해지면 PG 어댑터로 교체."""

    async def record(self, subject: str, note: str) -> None:
        logger.info("[herald-record] %s | %s", subject, note)
