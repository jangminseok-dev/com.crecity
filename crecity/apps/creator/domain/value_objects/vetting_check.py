from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from creator.domain.entities.profile_analytics_entity import ProfileAnalytics


@dataclass(frozen=True, slots=True)
class VettingCheck:
    """프로필 심사 자동 체크(갭 #16) — 자가입력 지표가 정량 기준을 넘는지 본다.

    **판정을 대신하지 않는다.** 자가입력 + 스크린샷이라 위조가 가능하므로,
    운영자가 스크린샷을 보고 최종 승인·반려한다(체크는 참고선).
    기준값은 주입받는다 — 도메인은 정책 수치를 소유하지 않는다(core/config가 정본).
    """

    platform_count: int
    total_followers: int
    best_engagement_permille: int | None  # 등록 채널 중 최고 참여율(‰) — 미입력이면 None
    min_followers: int
    min_engagement_permille: int

    @classmethod
    def of(
        cls,
        analytics: list[ProfileAnalytics],
        min_followers: int,
        min_engagement_permille: int,
    ) -> VettingCheck:
        rates = [a.engagement_permille for a in analytics if a.engagement_permille is not None]
        return cls(
            platform_count=len(analytics),
            total_followers=sum(a.followers_count for a in analytics),
            best_engagement_permille=max(rates) if rates else None,
            min_followers=min_followers,
            min_engagement_permille=min_engagement_permille,
        )

    @property
    def has_analytics(self) -> bool:
        return self.platform_count > 0

    @property
    def followers_ok(self) -> bool:
        return self.total_followers >= self.min_followers

    @property
    def engagement_ok(self) -> bool:
        return (
            self.best_engagement_permille is not None
            and self.best_engagement_permille >= self.min_engagement_permille
        )

    @property
    def passed(self) -> bool:
        return self.has_analytics and self.followers_ok and self.engagement_ok
