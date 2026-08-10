from dataclasses import dataclass


@dataclass(frozen=True)
class OrderPlacementCommand:

    package_id: int
    requirements: str
    brand_user_id: int  # 로그인 사용자 (허브 계약으로 검증됨)
    account_type: str  # BRAND만 주문 가능


@dataclass(frozen=True)
class CustomOrderPlacementCommand:

    offer_id: int
    requirements: str
    brand_user_id: int
    account_type: str  # BRAND만 주문 가능
