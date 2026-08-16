"""캠페인 도메인 이벤트 빌더(갭 #73).

이벤트는 지원 저장과 같은 트랜잭션에 적재된다(리포지토리가 담당, BOUNDARIES §1).
"""

from __future__ import annotations

from hub.app.dtos.outbox_event_dto import OutboxEvent


def application_received_event(
    campaign_id: int, brand_user_id: int, campaign_title: str, creator_name: str
) -> OutboxEvent:
    return OutboxEvent(
        event_type="campaign.application_received",
        payload={
            "campaign_id": campaign_id,
            "brand_user_id": brand_user_id,
            "campaign_title": campaign_title,
            "creator_name": creator_name,
        },
    )
