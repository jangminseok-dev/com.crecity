from dataclasses import dataclass


@dataclass(frozen=True)
class CheckoutCommand:

    package_id: int
    requirements: str
    brand_user_id: int  # 로그인 사용자 (허브 계약으로 검증됨)
    account_type: str  # BRAND만 결제 가능
    use_credit: bool = False  # 보유 크레딧을 결제에 사용할지 — 적용액은 서버가 확정


@dataclass(frozen=True)
class OfferCheckoutCommand:

    offer_id: int
    requirements: str
    brand_user_id: int
    account_type: str  # BRAND만 결제 가능
    use_credit: bool = False


@dataclass(frozen=True)
class ApplicationCheckoutCommand:
    """캠페인 지원 수락 결제 준비 — 견적·당사자는 허브 CampaignApplicationPort로 해석."""

    application_id: int
    requirements: str
    brand_user_id: int
    account_type: str  # BRAND만 결제 가능
    use_credit: bool = False


@dataclass(frozen=True)
class CartCheckoutCommand:
    """장바구니 일괄 결제 준비(§3.8) — 항목별 가격은 서버가 전부 재확정한다."""

    package_ids: tuple[int, ...]
    requirements: str  # 일괄 결제 공통 브리프
    brand_user_id: int
    account_type: str  # BRAND만 결제 가능
    use_credit: bool = False


@dataclass(frozen=True)
class CheckoutResult:
    """프론트 결제창(SDK) 호출 파라미터 — 금액은 서버 확정값이다.

    pg_amount_krw가 0이면(전액 크레딧) 결제창 없이 바로 승인(confirm)으로 간다.
    """

    pg_order_id: str
    amount_krw: int  # 결제 총액(크레딧 포함 전체)
    credit_applied_krw: int  # 크레딧 사용분
    pg_amount_krw: int  # 결제창에 청구할 금액 = amount_krw − credit_applied_krw
    order_name: str  # 결제창 표시용(패키지 제목)
    client_key: str  # 토스 클라이언트 키(공개 키)
