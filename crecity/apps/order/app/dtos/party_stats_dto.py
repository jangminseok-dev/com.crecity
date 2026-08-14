from dataclasses import dataclass


@dataclass(frozen=True)
class PartyTradeStats:
    """거래 상대를 판단하기 위한 이력 요약(갭 #65·#66).

    상태 전이 시각을 따로 남기지 않으므로 '평균 승인 소요' 같은 시간 지표는 낼 수 없다.
    지금 세는 것은 주문 테이블에 실제로 있는 값뿐이다.
    """

    total_orders: int
    completed_orders: int
    cancelled_orders: int  # 양측 합의 취소
    refunded_orders: int  # 거절·수락 만료 환불
    accept_expired_orders: int  # 그중 무응답 만료(크리에이터 신뢰 지표)
    total_revisions: int  # 완료·진행 주문에서 요청된 수정 횟수 합

    @property
    def has_history(self) -> bool:
        return self.total_orders > 0
