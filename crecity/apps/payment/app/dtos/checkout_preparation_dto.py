from dataclasses import dataclass


@dataclass(frozen=True)
class CheckoutCommand:

    package_id: int
    requirements: str
    brand_user_id: int  # 로그인 사용자 (허브 계약으로 검증됨)
    account_type: str  # BRAND만 결제 가능


@dataclass(frozen=True)
class CheckoutResult:
    """프론트 결제창(SDK) 호출 파라미터 — 금액은 서버 확정값이다."""

    pg_order_id: str
    amount_krw: int
    order_name: str  # 결제창 표시용(패키지 제목)
    client_key: str  # 토스 클라이언트 키(공개 키)
