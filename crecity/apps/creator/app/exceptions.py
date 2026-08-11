class DuplicateSlugError(Exception):
    """이미 사용 중인 슬러그로 등록 시도 — 라우터에서 409로 변환."""


class ProfileNotFoundError(Exception):
    """슬러그에 해당하는 프로필 없음 — 라우터에서 404로 변환."""


class PackageNotFoundError(Exception):
    """id에 해당하는 패키지 없음 — 라우터에서 404로 변환."""


class NotCreatorAccountError(Exception):
    """크리에이터 계정이 아닌 사용자의 프로필 등록 시도 — 라우터에서 403으로 변환."""


class DuplicateProfileError(Exception):
    """이미 프로필을 가진 계정의 재등록 시도(1인 1프로필) — 라우터에서 409로 변환."""


class NotProfileOwnerError(Exception):
    """소유자가 아닌 사용자의 쓰기 시도 — 라우터에서 403으로 변환."""


class PortfolioItemNotFoundError(Exception):
    """id에 해당하는 포트폴리오 항목 없음 — 라우터에서 404로 변환."""


class AnalyticsNotFoundError(Exception):
    """해당 플랫폼의 분석 지표 없음 — 라우터에서 404로 변환."""


class PortfolioLimitExceededError(Exception):
    """프로필당 포트폴리오 상한 초과 — 라우터에서 409로 변환."""
