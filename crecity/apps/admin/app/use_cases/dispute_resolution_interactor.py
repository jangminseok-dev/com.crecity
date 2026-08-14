from __future__ import annotations

from admin.app.dtos.dispute_resolution_dto import DisputeDecisionCommand
from admin.app.exceptions import DisputeTargetNotFoundError
from admin.app.ports.input.dispute_resolution_use_case import DisputeResolutionUseCase
from admin.app.ports.output.dispute_record_port import DisputeRecordPort
from hub.app.dtos.dispute_resolution_dto import DisputeSummary
from hub.app.ports.output.dispute_resolution_port import DisputeResolutionPort

_DECISION_LABELS = {
    "REFUND": "브랜드 전액 환불(주문 취소)",
    "RELEASE": "크리에이터 전액 지급(구매 확정)",
    "DISMISS": "기각(주문 유지)",
}


class DisputeResolutionInteractor(DisputeResolutionUseCase):

    def __init__(self, disputes: DisputeResolutionPort, record: DisputeRecordPort) -> None:
        self._disputes = disputes
        self._record = record

    async def list_open(self) -> list[DisputeSummary]:
        return await self._disputes.list_open()

    async def list_resolved(self) -> list[DisputeSummary]:
        # 판정 이력은 읽기만 한다 — 되돌리기는 없다(감사 기록과 같은 성격)
        return await self._disputes.list_resolved()

    async def resolve(self, command: DisputeDecisionCommand) -> DisputeSummary:
        result = await self._disputes.resolve(
            command.dispute_id, command.resolution, command.operator_id
        )
        if result is None:
            raise DisputeTargetNotFoundError(
                f"처리 대상 분쟁을 찾을 수 없습니다: {command.dispute_id}"
            )
        decision = _DECISION_LABELS.get(command.resolution, command.resolution)
        await self._record.record(
            subject="dispute_resolution",
            note=(
                f"분쟁 {result.id}(주문 {result.order_id}, {result.brand_total_krw}원) {decision} — "
                f"처리자 {command.operator_email}(user_id={command.operator_id})"
            ),
        )
        return result
