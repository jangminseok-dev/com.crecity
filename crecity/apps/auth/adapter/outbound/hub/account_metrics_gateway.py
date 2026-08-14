from __future__ import annotations

from sqlalchemy import func, select

from auth.adapter.outbound.orm.user_orm import UserOrm
from auth.domain.entities.user_entity import AccountType
from core.database import session_scope
from hub.app.dtos.platform_metrics_dto import AccountMetrics
from hub.app.ports.output.platform_metrics_port import AccountMetricsPort


class AuthAccountMetricsGateway(AccountMetricsPort):
    """허브 AccountMetricsPort 계약의 auth 구현(운영 대시보드, 갭 #55).

    탈퇴 계정(`deleted_at` 있음)은 제외한다 — 운영자가 보는 건 현재 활성 가입자다.
    """

    async def get_account_metrics(self) -> AccountMetrics:
        async with session_scope() as session:
            result = await session.execute(
                select(UserOrm.account_type, func.count())
                .where(UserOrm.deleted_at.is_(None))
                .group_by(UserOrm.account_type)
            )
            counts = {account_type: int(count) for account_type, count in result.all()}
        creators = counts.get(AccountType.CREATOR.value, 0)
        brands = counts.get(AccountType.BRAND.value, 0)
        # total은 합이 아니라 전체 — 새 계정 유형이 생겨도 누락되지 않게 한다
        return AccountMetrics(
            total_users=sum(counts.values()), creator_users=creators, brand_users=brands
        )
