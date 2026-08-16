from __future__ import annotations

from notification.app.dtos.outbox_relay_dto import (
    NotificationDraft,
    OutboxRecord,
    RelayResult,
)
from notification.app.ports.input.outbox_relay_use_case import OutboxRelayUseCase
from notification.app.ports.output.relay_store import RelayStore

_BATCH_LIMIT = 100


def _order_link(payload: dict) -> str:
    return f"/dashboard/orders/{payload.get('order_id')}"


def _to_drafts(record: OutboxRecord) -> list[NotificationDraft]:
    """이벤트 → 알림 변환 규칙(수신자·문구·링크). 미지의 타입은 빈 목록(발행 마킹만 — 전방 호환)."""
    t, p = record.event_type, record.payload
    title = p.get("package_title", "")
    if t == "order.placed":
        return [NotificationDraft(p["creator_user_id"], t, f"새 주문이 도착했습니다: {title}", _order_link(p))]
    if t == "order.accepted":
        return [NotificationDraft(p["brand_user_id"], t, f"주문이 수락되었습니다: {title}", _order_link(p))]
    if t == "order.rejected":
        return [NotificationDraft(p["brand_user_id"], t, f"주문이 거절·환불되었습니다(크레딧 적립): {title}", _order_link(p))]
    if t == "order.submitted":
        return [NotificationDraft(p["brand_user_id"], t, f"콘텐츠가 제출되었습니다 — 72시간 내 검토해 주세요: {title}", _order_link(p))]
    if t == "withdrawal.paid":
        # 인출 지급 완료(갭 #74) — 실지급액(원천징수 후)을 그대로 알려준다
        return [
            NotificationDraft(
                p["creator_user_id"], t,
                f"인출 {p['payout_krw']:,}원이 지급되었습니다",
                "/dashboard/balance",
            )
        ]
    if t == "withdrawal.failed":
        # 실패 시 잔액이 조용히 복원된다 — 복원 사실까지 알려야 잔액 변화가 설명된다
        return [
            NotificationDraft(
                p["creator_user_id"], t,
                f"인출 {p['amount_krw']:,}원이 처리되지 않아 잔액으로 복원되었습니다",
                "/dashboard/balance",
            )
        ]
    if t == "chat.message_received":
        # 새 메시지(갭 #72) — 상대가 이미 안 읽은 게 있으면 chat이 아예 발행하지 않는다
        sender = p.get("sender_name") or "상대방"
        return [
            NotificationDraft(
                p["recipient_user_id"],
                t,
                f"{sender}님이 메시지를 보냈습니다",
                f"/chat/{p['conversation_id']}",
            )
        ]
    if t == "order.deadline_soon":
        # 마감 때문에 움직여야 하는 쪽만 받는다(수락 대기=크리에이터, 검토 대기=브랜드)
        hours = p.get("hours_left")
        remain = f"{hours}시간" if isinstance(hours, int) else "곧"
        action = "수락 여부를 결정" if p.get("order_status") == "PENDING_ACCEPT" else "검토"
        return [
            NotificationDraft(
                p["recipient_user_id"],
                t,
                f"마감까지 {remain} 남았습니다 — {action}해 주세요: {title}",
                _order_link(p),
            )
        ]
    if t == "order.revision_requested":
        return [NotificationDraft(p["creator_user_id"], t, f"수정 요청이 도착했습니다: {title}", _order_link(p))]
    if t == "order.completed":
        payout = p.get("payout_krw")
        suffix = f" — {payout:,}원 적립" if isinstance(payout, int) else ""
        return [NotificationDraft(p["creator_user_id"], t, f"구매가 확정되었습니다{suffix}: {title}", _order_link(p))]
    if t == "order.cancel_requested":
        # 수신자 = 요청자의 상대방
        recipient = (
            p["creator_user_id"] if p.get("requested_by") == p["brand_user_id"] else p["brand_user_id"]
        )
        return [NotificationDraft(recipient, t, f"주문 취소 요청이 도착했습니다 — 동의 여부를 선택해 주세요: {title}", _order_link(p))]
    if t == "order.cancelled":
        return [
            NotificationDraft(p["brand_user_id"], t, f"주문이 합의 취소되었습니다(전액 크레딧 환불): {title}", _order_link(p)),
            NotificationDraft(p["creator_user_id"], t, f"주문이 합의 취소되었습니다: {title}", _order_link(p)),
        ]
    if t == "order.cancel_declined":
        return [NotificationDraft(p["requested_by"], t, f"취소 요청이 거부되어 주문이 계속 진행됩니다: {title}", _order_link(p))]
    if t == "order.dispute_raised":
        # 수신자 = 신고자의 상대방
        recipient = (
            p["creator_user_id"] if p.get("raised_by") == p["brand_user_id"] else p["brand_user_id"]
        )
        return [NotificationDraft(recipient, t, f"분쟁이 접수되었습니다 — 운영자가 검토합니다: {title}", _order_link(p))]
    if t == "order.dispute_resolved":
        outcome = {
            "REFUND": "브랜드 전액 환불로 종결되었습니다",
            "RELEASE": "크리에이터 전액 지급으로 종결되었습니다",
            "DISMISS": "기각되어 주문이 그대로 진행됩니다",
        }.get(str(p.get("resolution")), "처리되었습니다")
        return [
            NotificationDraft(p["brand_user_id"], t, f"분쟁이 {outcome}: {title}", _order_link(p)),
            NotificationDraft(p["creator_user_id"], t, f"분쟁이 {outcome}: {title}", _order_link(p)),
        ]
    if t == "profile.approved":
        return [NotificationDraft(p["creator_user_id"], t, "프로필 심사가 승인되었습니다 — 마켓 목록에 노출됩니다.", "/dashboard/profile")]
    if t == "profile.rejected":
        return [NotificationDraft(p["creator_user_id"], t, "프로필 심사가 반려되었습니다 — 내용을 보완해 보세요.", "/dashboard/profile")]
    return []


class OutboxRelayInteractor(OutboxRelayUseCase):

    def __init__(self, store: RelayStore) -> None:
        self._store = store

    async def relay(self) -> RelayResult:
        records = await self._store.fetch_unpublished(_BATCH_LIMIT)
        if not records:
            return RelayResult(consumed_events=0, created_notifications=0)
        drafts: list[NotificationDraft] = []
        for record in records:
            drafts.extend(_to_drafts(record))
        await self._store.publish([r.id for r in records], drafts)
        return RelayResult(consumed_events=len(records), created_notifications=len(drafts))
