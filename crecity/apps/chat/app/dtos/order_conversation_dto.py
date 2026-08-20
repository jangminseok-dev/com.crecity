from dataclasses import dataclass


@dataclass(frozen=True)
class OpenOrderConversationCommand:
    """주문 당사자 간 대화 열기(갭 #95) — 쌍당 1개(있으면 재사용).

    일반 문의(conversation_opening)는 브랜드만 시작할 수 있지만(콜드 DM 방지),
    주문이 있는 사이라면 크리에이터도 열 수 있다 — 거래 중 소통이 플랫폼 밖으로
    새지 않게 한다(§3.3).
    """

    order_id: int
    requester_user_id: int
