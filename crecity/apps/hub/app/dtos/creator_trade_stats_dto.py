from dataclasses import dataclass


@dataclass(frozen=True)
class CreatorTradeStats:
    """크리에이터 거래 이력 요약(갭 #66·#80) — order → creator 허브 계약.

    브랜드가 "이 사람이 답을 할까"를 판단하는 신호다. 건수는 전 기간,
    응답 속도는 전이 이력(갭 #79) 기반이라 도입 이후 데이터만 반영된다.
    """

    completed_orders: int
    accepted_orders: int  # 수락해 진행된 주문(완료·진행·검토·취소 합)
    received_orders: int  # 받은 주문 전체
    accept_expired_orders: int  # 무응답으로 만료된 주문
    # 응답 지표(갭 #80) — 이력 표본이 없으면 None / False. 배지 판정은 order가 소유
    avg_accept_hours: float | None = None
    fast_responder: bool = False
    # 분쟁 환불 판정(패소) 수(갭 #81) — 신뢰 배지 판정 재료(공개 수치로는 노출하지 않는다)
    dispute_refund_orders: int = 0
