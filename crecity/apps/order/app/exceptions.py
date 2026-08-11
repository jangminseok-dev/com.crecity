class NotBrandAccountError(Exception):
    """브랜드 계정이 아닌 사용자의 주문 시도 — 라우터에서 403으로 변환."""


class PackageNotOrderableError(Exception):
    """존재하지 않거나 주문 불가한 패키지 — 라우터에서 404로 변환."""


class OrderNotFoundError(Exception):
    """id에 해당하는 주문 없음 — 라우터에서 404로 변환."""


class NotOrderParticipantError(Exception):
    """주문 당사자(브랜드·크리에이터)가 아닌 조회 시도 — 라우터에서 403으로 변환."""


class NotCreatorAccountError(Exception):
    """크리에이터 계정이 아닌 인출 시도 — 라우터에서 403으로 변환."""


class InsufficientBalanceError(Exception):
    """잔액보다 큰 인출 요청 — 라우터에서 409로 변환."""


class WithdrawalNotFoundError(Exception):
    """id에 해당하는 인출 요청 없음 — 라우터에서 404로 변환."""


class InsufficientCreditError(Exception):
    """주문 생성 시점 크레딧 잔액 부족(준비~승인 사이 소진) — 게이트웨이가 None으로 변환해 PG 취소 보정."""
