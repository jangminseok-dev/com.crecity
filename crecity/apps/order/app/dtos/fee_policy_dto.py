from dataclasses import dataclass


@dataclass(frozen=True)
class FeePolicyResult:
    """공개 수수료 안내(갭 #62) — 지금 적용 중인 값을 그대로 내려준다.

    화면이 숫자를 하드코딩하지 않게 하려는 것이 목적이다(설정이 바뀌면 화면도 따라온다).
    실제 주문에는 **주문 생성 시점 값이 스냅샷**되므로 이 값은 '앞으로 만들 주문' 기준이다.
    """

    brand_fee_percent: int
    creator_fee_percent: int
    withdrawal_tax_permille: int
    response_deadline_hours: int
