class NotBrandAccountError(Exception):
    """브랜드 계정이 아닌 사용자의 주문 시도 — 라우터에서 403으로 변환."""


class PackageNotOrderableError(Exception):
    """존재하지 않거나 주문 불가한 패키지 — 라우터에서 404로 변환."""


class OrderNotFoundError(Exception):
    """id에 해당하는 주문 없음 — 라우터에서 404로 변환."""


class NotOrderParticipantError(Exception):
    """주문 당사자(브랜드·크리에이터)가 아닌 조회 시도 — 라우터에서 403으로 변환."""
