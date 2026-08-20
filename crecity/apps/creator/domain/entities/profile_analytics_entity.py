from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from creator.domain.value_objects.audience_breakdown import AudienceShare

# 분석 지표를 받는 채널 — 패키지 플랫폼에서 채널이 아닌 UGC를 제외한 목록(§9.2)
ANALYTICS_PLATFORMS: tuple[str, ...] = ("INSTAGRAM", "YOUTUBE", "TIKTOK", "NAVER_BLOG")


@dataclass(frozen=True, slots=True)
class ProfileAnalytics:
    """채널 분석 지표 — 초기엔 자가입력 + 스크린샷 인증(§9.2, API 연동은 갭 #43 후속).

    engagement_permille는 참여율 ×10 정수(3.5% → 35) — 부동소수 대신 정수 보관.
    """

    id: int
    profile_id: int
    platform: str  # ANALYTICS_PLATFORMS 중 하나
    followers_count: int
    engagement_permille: int | None  # 미입력 허용
    screenshot_file_name: str  # 자가입력 증빙 스크린샷(필수)
    avg_views: int | None = None  # 평균 조회수(갭 #102) — 선택·자가입력
    updated_at: datetime | None = None
    # 오디언스(§2.1-6, 갭 #67) — 지역은 단일 값, 연령·성별 비율은 별도 행
    top_audience_region: str | None = None
    audience: tuple[AudienceShare, ...] = ()
    # 이상치 플래그 사유(갭 #82) — None이면 정상. 내부 운영 신호(공개 응답 미노출)
    flag_reason: str | None = None
