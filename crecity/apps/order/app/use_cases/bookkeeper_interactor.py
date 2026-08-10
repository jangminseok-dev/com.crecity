from __future__ import annotations

from order.app.dtos.bookkeeper_dto import BookkeeperQuery, BookkeeperResponse
from order.app.ports.input.bookkeeper_use_case import BookkeeperUseCase
from order.app.ports.output.bookkeeper_record_port import BookkeeperRecordPort


class BookkeeperInteractor(BookkeeperUseCase):
    """주문 (order) 대장 — 담당: 주문 상태머신·에스크로/잔액 원장(돈의 장부)."""

    def __init__(self, record: BookkeeperRecordPort) -> None:
        self._record = record

    async def introduce_myself(self, query: BookkeeperQuery) -> BookkeeperResponse:
        await self._record.record(subject="introduce_myself", note=f"{query.name} 자기소개 관찰")
        return BookkeeperResponse(
            id=query.id,
            name=query.name,
            introduction=(
                "주문과 돈의 장부를 담당합니다. 제공 엔드포인트: POST /order/orders(주문 생성, 브랜드만), "
                "POST /order/orders/{id}/accept·reject·submit·request-revision·approve(상태 전이), "
                "GET /order/orders(내 주문)·GET /order/orders/{id}(상세, 당사자만)·GET /order/balance(내 잔액). "
                "수수료율은 주문 시점 스냅샷, 72h 만료는 주기 스캔이 전이합니다. "
                "PG 결제·인출은 payment 앱 예정입니다."
            ),
        )
