from dataclasses import dataclass


@dataclass(frozen=True)
class OutboxEvent:
    """도메인 이벤트 초안 — 발행 스포크가 상태 변경과 같은 트랜잭션에 적재한다(BOUNDARIES §1).

    event_type 규약: "<도메인>.<사건>" (예: "order.placed", "profile.approved").
    payload는 JSON 직렬화 가능한 dict — 소비자(notification)가 수신자·문구를 결정한다.
    """

    event_type: str
    payload: dict
