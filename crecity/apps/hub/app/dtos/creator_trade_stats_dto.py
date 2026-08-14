from dataclasses import dataclass


@dataclass(frozen=True)
class CreatorTradeStats:
    """크리에이터 거래 이력 요약(갭 #66) — order → creator 허브 계약.

    브랜드가 "이 사람이 답을 할까"를 판단하는 신호다. 응답 소요 시간은 상태 전이 시각을
    남기지 않아 계산할 수 없으므로, 셀 수 있는 건수만 싣는다.
    """

    completed_orders: int
    accepted_orders: int  # 수락해 진행된 주문(완료·진행·검토·취소 합)
    received_orders: int  # 받은 주문 전체
    accept_expired_orders: int  # 무응답으로 만료된 주문
