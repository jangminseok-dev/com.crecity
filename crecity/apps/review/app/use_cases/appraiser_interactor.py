from __future__ import annotations

from review.app.dtos.appraiser_dto import AppraiserQuery, AppraiserResponse
from review.app.ports.input.appraiser_use_case import AppraiserUseCase
from review.app.ports.output.appraiser_record_port import AppraiserRecordPort


class AppraiserInteractor(AppraiserUseCase):
    """리뷰 (review) 대장 — 담당: 3축 평점(소통·기한·만족)·리뷰 블러 정책."""

    def __init__(self, record: AppraiserRecordPort) -> None:
        self._record = record

    async def introduce_myself(self, query: AppraiserQuery) -> AppraiserResponse:
        await self._record.record(subject="introduce_myself", note=f"{query.name} 자기소개 관찰")
        return AppraiserResponse(
            id=query.id,
            name=query.name,
            introduction=(
                "거래 신뢰를 담당합니다. 제공 엔드포인트: POST /review/orders/{id}/review"
                "(완료 주문의 브랜드가 3축 평점·리뷰 작성, 주문당 1회), "
                "GET /review/creators/{slug}(공개 집계 — 원문은 로그인 시에만, 블러 정책). "
                "예정: 리뷰 신고·운영 중재."
            ),
        )
