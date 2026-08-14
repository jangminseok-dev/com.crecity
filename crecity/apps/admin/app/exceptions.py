class ReviewTargetNotFoundError(Exception):
    """심사 대상 프로필 없음 — 라우터에서 404로 변환."""


class SettlementTargetNotFoundError(Exception):
    """처리 대상 인출 없음 — 라우터에서 404로 변환."""


class DisputeTargetNotFoundError(Exception):
    """처리 대상 분쟁 없음(또는 주문 유실) — 라우터에서 404로 변환."""


class ReportTargetNotFoundError(Exception):
    """처리 대상 신고 없음 — 라우터에서 404로 변환."""


class DuplicateReportError(Exception):
    """같은 대상에 처리 대기 중인 신고를 또 낸 경우 — 라우터에서 409로 변환."""
