from dataclasses import dataclass


@dataclass(frozen=True)
class BalanceQuery:

    user_id: int


@dataclass(frozen=True)
class BalanceResult:

    user_id: int
    balance_krw: int  # 크리에이터 적립 + 브랜드 환불 크레딧 합(차감 유형은 인출 도입 시)
