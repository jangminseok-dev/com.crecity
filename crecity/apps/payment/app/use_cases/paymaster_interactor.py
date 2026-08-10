from __future__ import annotations

from payment.app.dtos.paymaster_dto import PaymasterQuery, PaymasterResponse
from payment.app.ports.input.paymaster_use_case import PaymasterUseCase
from payment.app.ports.output.paymaster_record_port import PaymasterRecordPort


class PaymasterInteractor(PaymasterUseCase):
    """결제 (payment) 대장 — 담당: 돈이 시스템 밖과 만나는 지점(PG 승인·인출·세무)."""

    def __init__(self, record: PaymasterRecordPort) -> None:
        self._record = record

    async def introduce_myself(self, query: PaymasterQuery) -> PaymasterResponse:
        await self._record.record(subject="introduce_myself", note=f"{query.name} 자기소개 관찰")
        return PaymasterResponse(
            id=query.id,
            name=query.name,
            introduction=(
                "외부 결제 접점을 담당합니다. 제공 엔드포인트: POST /payment/checkouts(결제 준비 — "
                "서버 금액 확정), POST /payment/confirm(토스페이먼츠 승인 → 주문 생성, 실패 시 취소 보정). "
                "원장은 order 소유이며 저는 PG 승인 기록만 가집니다. "
                "예정: 크리에이터 인출(pay-out) · 원천징수 3.3% · 지급명세서."
            ),
        )
