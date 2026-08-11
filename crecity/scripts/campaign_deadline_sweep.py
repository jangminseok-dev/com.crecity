"""공고 지원 마감일 스캔 — cron이 주기 실행한다(§3.2, 갭 #27).

실행:
    cd crecity && PYTHONPATH=.:apps ../.venv/bin/python scripts/campaign_deadline_sweep.py

crontab 예 (10분 주기):
    */10 * * * * cd <repo>/crecity && PYTHONPATH=.:apps ../.venv/bin/python scripts/campaign_deadline_sweep.py
"""

import asyncio
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "apps"))

from campaign.adapter.outbound.pg.campaign_pg_repository import (  # noqa: E402
    CampaignPgRepository,
)
from campaign.app.use_cases.campaign_deadline_sweep_interactor import (  # noqa: E402
    CampaignDeadlineSweepInteractor,
)
from core.database import dispose_engine, init_engine, session_scope  # noqa: E402


async def main() -> None:
    init_engine()
    try:
        async with session_scope() as session:
            result = await CampaignDeadlineSweepInteractor(
                CampaignPgRepository(session)
            ).sweep()
        for campaign_id in result.closed_campaign_ids:
            print(f"공고 {campaign_id} → CLOSED (마감일 경과)")
        print(f"자동 마감 {len(result.closed_campaign_ids)}건")
    finally:
        await dispose_engine()


if __name__ == "__main__":
    asyncio.run(main())
