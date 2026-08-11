from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime, timedelta
from enum import StrEnum

from order.domain.entities.ledger_entry_entity import LedgerEntryDraft, LedgerEntryType


class OrderStatus(StrEnum):
    """주문 상태머신 (BOUNDARIES §4 · collabstr-analysis §3.8).

    PENDING_ACCEPT ──수락──▶ IN_PROGRESS ──제출──▶ IN_REVIEW ──승인/72h──▶ COMPLETED
          │                                     │
          ├─ 거절/72h 만료 ─▶ REFUNDED           └─ 수정 요청 ─▶ IN_PROGRESS (무제한)
    """

    PENDING_ACCEPT = "PENDING_ACCEPT"
    IN_PROGRESS = "IN_PROGRESS"
    IN_REVIEW = "IN_REVIEW"
    COMPLETED = "COMPLETED"
    REFUNDED = "REFUNDED"
    CANCELLED = "CANCELLED"  # 양측 합의 취소 — 전이 로직은 취소 슬라이스 도입 시


class InvalidOrderTransitionError(Exception):
    """현재 상태에서 허용되지 않는 전이 — 라우터에서 409로 변환."""


class NotOrderActorError(Exception):
    """해당 전이의 권한자가 아님(브랜드 전이를 크리에이터가 시도 등) — 라우터에서 403으로 변환."""


@dataclass(frozen=True, slots=True)
class Order:
    """주문 도메인 엔티티 — 전이·수수료 계산은 순수 파이썬(스텁 없이 단위 테스트 가능).

    금액·수수료율은 주문 생성 시점 스냅샷(§7-4 — 요율 변경 소급 차단).
    deadline_at은 '현재 상태의 마감시각'(PENDING_ACCEPT·IN_REVIEW에만 존재) —
    만료 전이는 주기 스캔이 expire()를 호출해 일어난다.
    """

    id: int
    package_id: int | None  # creator 패키지 논리 참조(DB FK 없음) — 커스텀 오퍼 주문은 None
    package_title: str  # 표시용 스냅샷(패키지 수정·삭제와 무관하게 주문 이력 보존)
    brand_user_id: int
    creator_user_id: int
    amount_krw: int  # 패키지 가격 스냅샷
    brand_fee_percent: int
    creator_fee_percent: int
    requirements: str  # 브랜드 요구사항 — 수정 요청 범위의 기준(collabstr §3.8)
    status: OrderStatus
    deadline_at: datetime | None
    created_at: datetime | None = None

    # ── 수수료 계산 (정수 원 단위, 내림 — 부동소수 금지) ──────────────────

    def brand_fee_krw(self) -> int:
        return self.amount_krw * self.brand_fee_percent // 100

    def creator_fee_krw(self) -> int:
        return self.amount_krw * self.creator_fee_percent // 100

    def brand_total_krw(self) -> int:
        """브랜드 결제 총액 = 패키지 가격 + 브랜드 수수료 (에스크로 예치액)."""
        return self.amount_krw + self.brand_fee_krw()

    def creator_payout_krw(self) -> int:
        """구매 확정 시 크리에이터 적립액 = 패키지 가격 − 크리에이터 수수료."""
        return self.amount_krw - self.creator_fee_krw()

    def platform_revenue_krw(self) -> int:
        return self.brand_fee_krw() + self.creator_fee_krw()

    # ── 전이 ──────────────────────────────────────────────────────────────

    def _require_status(self, expected: OrderStatus, action: str) -> None:
        if self.status is not expected:
            raise InvalidOrderTransitionError(
                f"{action}은(는) {expected.value} 상태에서만 가능합니다 (현재: {self.status.value})"
            )

    def _require_creator(self, actor_user_id: int) -> None:
        if actor_user_id != self.creator_user_id:
            raise NotOrderActorError("주문을 받은 크리에이터만 할 수 있는 동작입니다.")

    def _require_brand(self, actor_user_id: int) -> None:
        if actor_user_id != self.brand_user_id:
            raise NotOrderActorError("주문한 브랜드만 할 수 있는 동작입니다.")

    def accept(self, actor_user_id: int) -> Order:
        """크리에이터 수락 → 작업 시작. 에스크로는 예치 상태 유지."""
        self._require_creator(actor_user_id)
        self._require_status(OrderStatus.PENDING_ACCEPT, "수락")
        return replace(self, status=OrderStatus.IN_PROGRESS, deadline_at=None)

    def reject(self, actor_user_id: int) -> tuple[Order, list[LedgerEntryDraft]]:
        """크리에이터 거절 → 즉시 환불(브랜드 크레딧)."""
        self._require_creator(actor_user_id)
        self._require_status(OrderStatus.PENDING_ACCEPT, "거절")
        return self._refund()

    def submit(
        self,
        actor_user_id: int,
        now: datetime,
        review_deadline: timedelta,
        deliverable_count: int,
    ) -> Order:
        """크리에이터 콘텐츠 제출 → 브랜드 검토 대기(72h 마감 시작).

        제출은 상태 전이가 아니라 결과물 인도다 — 납품물이 없으면 제출 불가
        (에스크로 승인·분쟁 판단의 근거를 남긴다).
        """
        self._require_creator(actor_user_id)
        self._require_status(OrderStatus.IN_PROGRESS, "제출")
        if deliverable_count <= 0:
            raise InvalidOrderTransitionError("납품물(파일 또는 링크)을 먼저 등록해야 제출할 수 있습니다.")
        return replace(self, status=OrderStatus.IN_REVIEW, deadline_at=now + review_deadline)

    def ensure_can_attach_deliverable(self, actor_user_id: int) -> None:
        """납품물 등록 검증 — 작업 중(IN_PROGRESS)인 주문의 크리에이터만."""
        self._require_creator(actor_user_id)
        self._require_status(OrderStatus.IN_PROGRESS, "납품물 등록")

    def request_revision(self, actor_user_id: int) -> Order:
        """브랜드 수정 요청 → 재작업(원 요구사항 범위 내 무제한 — collabstr §3.8)."""
        self._require_brand(actor_user_id)
        self._require_status(OrderStatus.IN_REVIEW, "수정 요청")
        return replace(self, status=OrderStatus.IN_PROGRESS, deadline_at=None)

    def approve(self, actor_user_id: int) -> tuple[Order, list[LedgerEntryDraft]]:
        """브랜드 승인 → 구매 확정: 크리에이터 잔액 적립 + 플랫폼 수수료 확정."""
        self._require_brand(actor_user_id)
        self._require_status(OrderStatus.IN_REVIEW, "승인")
        return self._complete()

    def expire(self, now: datetime) -> tuple[Order, list[LedgerEntryDraft]] | None:
        """마감시각 경과 처리(주기 스캔 전용) — 대상 아니면 None.

        PENDING_ACCEPT 만료 → 자동 환불 · IN_REVIEW 만료 → 자동 승인(§3.8).
        """
        if self.deadline_at is None or now < self.deadline_at:
            return None
        if self.status is OrderStatus.PENDING_ACCEPT:
            return self._refund()
        if self.status is OrderStatus.IN_REVIEW:
            return self._complete()
        return None

    # ── 전이 결과 (원장 기입과 원자적으로 저장돼야 한다 — BOUNDARIES §1) ──

    def _refund(self) -> tuple[Order, list[LedgerEntryDraft]]:
        refunded = replace(self, status=OrderStatus.REFUNDED, deadline_at=None)
        entries = [
            LedgerEntryDraft(
                entry_type=LedgerEntryType.BRAND_CREDIT_REFUND,
                user_id=self.brand_user_id,
                amount_krw=self.brand_total_krw(),
            )
        ]
        return refunded, entries

    def _complete(self) -> tuple[Order, list[LedgerEntryDraft]]:
        completed = replace(self, status=OrderStatus.COMPLETED, deadline_at=None)
        entries = [
            LedgerEntryDraft(
                entry_type=LedgerEntryType.CREATOR_EARNING,
                user_id=self.creator_user_id,
                amount_krw=self.creator_payout_krw(),
            ),
            LedgerEntryDraft(
                entry_type=LedgerEntryType.PLATFORM_REVENUE,
                user_id=None,
                amount_krw=self.platform_revenue_krw(),
            ),
        ]
        return completed, entries
