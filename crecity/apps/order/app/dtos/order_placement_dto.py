from dataclasses import dataclass


@dataclass(frozen=True)
class OrderPlacementCommand:

    package_id: int
    requirements: str
    brand_user_id: int  # 로그인 사용자 (허브 계약으로 검증됨)
    account_type: str  # BRAND만 주문 가능
    credit_used_krw: int = 0  # 체크아웃에서 확정된 크레딧 사용분 — 생성 시 잔액 재검증·차감


@dataclass(frozen=True)
class CustomOrderPlacementCommand:

    offer_id: int
    requirements: str
    brand_user_id: int
    account_type: str  # BRAND만 주문 가능
    credit_used_krw: int = 0  # 체크아웃에서 확정된 크레딧 사용분 — 생성 시 잔액 재검증·차감


@dataclass(frozen=True)
class ApplicationOrderPlacementCommand:
    """캠페인 지원 수락 주문 — 견적·당사자는 허브 CampaignApplicationPort로 해석."""

    application_id: int
    requirements: str
    brand_user_id: int
    account_type: str  # BRAND만 주문 가능
    credit_used_krw: int = 0


@dataclass(frozen=True)
class CartOrderPlacementCommand:
    """장바구니 일괄 주문(§3.8) — 패키지별 주문 N건을 단일 트랜잭션으로 생성한다."""

    package_ids: tuple[int, ...]  # 중복 제거된 패키지 목록
    requirements: str  # 일괄 결제 공통 브리프
    brand_user_id: int
    account_type: str  # BRAND만 주문 가능
    credit_used_krw: int = 0
