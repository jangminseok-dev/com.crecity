from __future__ import annotations

from core.database import session_scope
from creator.adapter.outbound.pg.creator_package_pg_repository import CreatorPackagePgRepository
from creator.adapter.outbound.pg.creator_profile_pg_repository import CreatorProfilePgRepository
from hub.app.dtos.package_summary_dto import PackageSummary
from hub.app.ports.output.package_summary_port import PackageSummaryPort


class CreatorPackageSummaryGateway(PackageSummaryPort):
    """허브 PackageSummaryPort 계약의 creator 구현 — main.py가 조립한다.

    호출자(order) 트랜잭션과 무관한 읽기 전용 조회라 자체 세션을 연다.
    """

    async def get_package_summary(self, package_id: int) -> PackageSummary | None:
        async with session_scope() as session:
            package = await CreatorPackagePgRepository(session).find_by_id(package_id)
            if package is None:
                return None
            profile = await CreatorProfilePgRepository(session).find_by_id(package.profile_id)
        if profile is None or profile.user_id is None:
            return None  # 소유 계정 없는 레거시 프로필 — 적립 대상이 없어 주문 불가
        return PackageSummary(
            package_id=package.id,
            title=package.title,
            price_krw=package.price_krw,
            creator_user_id=profile.user_id,
        )
