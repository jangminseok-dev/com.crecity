"""주문 72h 마감 스캔 — cron이 주기 실행한다(분 단위 정밀도면 충분, BOUNDARIES §4).

실행:
    cd crecity && PYTHONPATH=.:apps ../.venv/bin/python scripts/order_deadline_sweep.py

crontab 예 (5분 주기):
    */5 * * * * cd <repo>/crecity && PYTHONPATH=.:apps ../.venv/bin/python scripts/order_deadline_sweep.py
"""

import asyncio
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "apps"))

from core.database import dispose_engine, init_engine, session_scope  # noqa: E402
from order.adapter.outbound.pg.order_pg_repository import OrderPgRepository  # noqa: E402
from order.app.use_cases.deadline_sweep_interactor import DeadlineSweepInteractor  # noqa: E402


async def main() -> None:
    init_engine()
    try:
        async with session_scope() as session:
            result = await DeadlineSweepInteractor(OrderPgRepository(session)).sweep()
        if result.outcomes:
            for outcome in result.outcomes:
                print(f"주문 {outcome.order_id} → {outcome.status}")
        print(f"만료 전이 {len(result.outcomes)}건")
    finally:
        await dispose_engine()


if __name__ == "__main__":
    asyncio.run(main())
