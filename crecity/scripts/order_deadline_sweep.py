"""주문 72h 마감 스캔 — cron이 주기 실행한다(분 단위 정밀도면 충분, BOUNDARIES §4).

만료 전이와 함께 **마감 임박 알림**(갭 #76)도 보낸다 — 지나기 전에 한 번 알려
무응답 만료(랭킹 페널티)를 줄인다.

실행:
    cd crecity && PYTHONPATH=.:apps ../.venv/bin/python scripts/order_deadline_sweep.py

crontab 예 (5분 주기):
    */5 * * * * cd <repo>/crecity && PYTHONPATH=.:apps ../.venv/bin/python scripts/order_deadline_sweep.py
"""

import asyncio
import os
import sys
from datetime import timedelta

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "apps"))

from core.config import ORDER_DEADLINE_WARNING_HOURS  # noqa: E402
from core.database import dispose_engine, init_engine, session_scope  # noqa: E402
from order.adapter.outbound.pg.order_pg_repository import OrderPgRepository  # noqa: E402
from order.app.use_cases.deadline_sweep_interactor import DeadlineSweepInteractor  # noqa: E402


async def main() -> None:
    init_engine()
    try:
        async with session_scope() as session:
            result = await DeadlineSweepInteractor(
                OrderPgRepository(session),
                warning_threshold=timedelta(hours=ORDER_DEADLINE_WARNING_HOURS),
            ).sweep()
        if result.outcomes:
            for outcome in result.outcomes:
                print(f"주문 {outcome.order_id} → {outcome.status}")
        warned = result.warned_order_ids or []
        if warned:
            print(f"마감 임박 알림 {len(warned)}건: {warned}")
        print(f"만료 전이 {len(result.outcomes)}건 · 임박 알림 {len(warned)}건")
    finally:
        await dispose_engine()


if __name__ == "__main__":
    asyncio.run(main())
