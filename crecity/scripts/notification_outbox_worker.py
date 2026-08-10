"""Outbox 릴레이 워커 — 미발행 이벤트를 인앱 알림으로 변환한다(BOUNDARIES §1 Outbox).

크래시에 안전: 발행 마킹 전 죽으면 다음 주기에 재처리된다(유실 없음).

실행:
    cd crecity && PYTHONPATH=.:apps ../.venv/bin/python scripts/notification_outbox_worker.py

crontab 예 (1분 주기):
    * * * * * cd <repo>/crecity && PYTHONPATH=.:apps ../.venv/bin/python scripts/notification_outbox_worker.py
"""

import asyncio
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "apps"))

from core.database import dispose_engine, init_engine, session_scope  # noqa: E402
from notification.adapter.outbound.pg.relay_pg_store import RelayPgStore  # noqa: E402
from notification.app.use_cases.outbox_relay_interactor import OutboxRelayInteractor  # noqa: E402


async def main() -> None:
    init_engine()
    try:
        async with session_scope() as session:
            result = await OutboxRelayInteractor(RelayPgStore(session)).relay()
        print(f"이벤트 {result.consumed_events}건 소비 → 알림 {result.created_notifications}건 생성")
    finally:
        await dispose_engine()


if __name__ == "__main__":
    asyncio.run(main())
