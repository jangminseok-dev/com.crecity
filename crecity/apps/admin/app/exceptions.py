class ReviewTargetNotFoundError(Exception):
    """심사 대상 프로필 없음 — 라우터에서 404로 변환."""


class SettlementTargetNotFoundError(Exception):
    """처리 대상 인출 없음 — 라우터에서 404로 변환."""
