class NotBrandAccountError(Exception):
    """브랜드 계정이 아닌 결제 시도 — 라우터에서 403으로 변환."""


class PackageNotOrderableError(Exception):
    """존재하지 않거나 주문 불가한 패키지 — 라우터에서 404로 변환."""


class PaymentIntentNotFoundError(Exception):
    """결제 의도 없음 — 라우터에서 404로 변환."""


class NotPaymentOwnerError(Exception):
    """본인 결제가 아닌 승인 시도 — 라우터에서 403으로 변환."""


class PaymentAlreadyProcessedError(Exception):
    """이미 처리된 결제의 재승인 시도 — 라우터에서 409로 변환."""


class PaymentAmountMismatchError(Exception):
    """결제 금액 불일치(위변조 의심) — 라우터에서 400으로 변환."""


class PaymentConfirmError(Exception):
    """PG 승인 실패 또는 승인 후 주문 생성 실패(보정 취소됨) — 라우터에서 502로 변환."""
