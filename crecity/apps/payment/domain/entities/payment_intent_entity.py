from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum


class PaymentIntentStatus(StrEnum):
    """결제 의도 상태 — 외부 PG는 원자적일 수 없으므로 시도 자체를 기록한다(BOUNDARIES §3).

    READY      결제창 호출 준비(금액 확정 스냅샷)
    CONFIRMED  PG 승인 + 주문 생성 완료
    FAILED     승인 실패 또는 주문 생성 실패(보정 취소 포함) — 사유 기록
    """

    READY = "READY"
    CONFIRMED = "CONFIRMED"
    FAILED = "FAILED"


@dataclass(frozen=True, slots=True)
class PaymentIntent:
    """결제 의도 — 결제창 호출 전 서버가 금액을 확정해 두는 기록(금액 위변조 방지).

    pg_order_id는 토스 orderId로 쓰는 우리 쪽 고유 문자열이다.
    """

    id: int
    pg_order_id: str
    package_id: int | None  # 커스텀 오퍼 결제는 None
    brand_user_id: int
    requirements: str  # 승인 후 주문 생성에 쓸 페이로드 보관
    amount_krw: int  # 결제 총액 스냅샷(크레딧 포함 전체) — 주문 생성 금액 대조에 쓴다
    status: PaymentIntentStatus
    credit_applied_krw: int = 0  # 체크아웃에서 확정한 크레딧 사용분 — PG 결제액 = 총액 − 이 값
    offer_id: int | None = None  # 커스텀 오퍼(chat) 논리 참조 — 패키지 결제는 None
    application_id: int | None = None  # 캠페인 지원(campaign) 논리 참조 — 지원 수락 결제만
    cart_package_ids: tuple[int, ...] = ()  # 장바구니 결제 항목(§3.8) — 단건 결제는 빈 튜플
    payment_key: str | None = None  # PG 결제 키(승인 후)
    order_id: int | None = None  # 생성된 주문(승인 후)
    failure_reason: str | None = None
    created_at: datetime | None = None

    def is_owned_by(self, user_id: int) -> bool:
        return self.brand_user_id == user_id

    def is_ready(self) -> bool:
        return self.status is PaymentIntentStatus.READY

    def pg_amount_krw(self) -> int:
        """PG에 실제 청구할 금액 = 총액 − 크레딧 사용분. 0이면 PG 호출 없이 승인한다."""
        return self.amount_krw - self.credit_applied_krw

    def matches_amount(self, amount_krw: int) -> bool:
        """리다이렉트 쿼리의 amount와 서버 확정 PG 결제액 대조 — 다르면 승인 금지(토스 문서 필수 절차)."""
        return self.pg_amount_krw() == amount_krw
