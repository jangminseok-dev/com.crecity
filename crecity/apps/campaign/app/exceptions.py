class CampaignNotFoundError(Exception):
    """공고 없음 — 라우터에서 404로 변환."""


class NotBrandAccountError(Exception):
    """브랜드 계정이 아닌 공고 등록 시도 — 라우터에서 403으로 변환."""


class NotCreatorAccountError(Exception):
    """크리에이터 계정이 아닌 지원 시도 — 라우터에서 403으로 변환."""


class CreatorProfileRequiredError(Exception):
    """프로필 없는 크리에이터의 지원 시도 — 라우터에서 403으로 변환."""


class AlreadyAppliedError(Exception):
    """공고당 1회 지원 위반 — 라우터에서 409로 변환."""
