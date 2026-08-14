from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime, timedelta
from enum import StrEnum

from order.domain.entities.ledger_entry_entity import LedgerEntryDraft, LedgerEntryType


class OrderStatus(StrEnum):
    """주문 상태머신 (BOUNDARIES §4 · collabstr-analysis §3.8).

    PENDING_ACCEPT ──수락──▶ IN_PROGRESS ──제출──▶ IN_REVIEW ──승인/72h──▶ COMPLETED
          │                                     │
          ├─ 거절/72h 만료 ─▶ REFUNDED           └─ 수정 요청 ─▶ IN_PROGRESS (revision_limit까지)
    """

    PENDING_ACCEPT = "PENDING_ACCEPT"
    IN_PROGRESS = "IN_PROGRESS"
    IN_REVIEW = "IN_REVIEW"
    COMPLETED = "COMPLETED"
    REFUNDED = "REFUNDED"
    CANCELLED = "CANCELLED"  # 합의 취소(요청→상대 동의) 또는 분쟁 환불 판정 — 둘 다 전액 환불


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
    cancel_requested_by: int | None = None  # 양측 합의 취소의 요청자 — 상대 동의·거부 대기 중
    # 표준계약 구조화 필드(§3.3·§9.2, 갭 #29) — 주문 생성 시 패키지에서 스냅샷
    accept_expired: bool = False  # 72h 내 미수락으로 환불된 주문 — 랭킹 페널티 대상(§3.8)
    revision_limit: int = 2  # 브랜드가 요청할 수 있는 수정 횟수(0이면 수정 불가)
    revisions_used: int = 0
    usage_rights: str = ""  # 2차 활용 범위
    created_at: datetime | None = None
    # 마감 임박 알림을 보낸 시각(갭 #76) — 중복 발송 방지 표식. 마감이 새로 잡히면 비운다
    deadline_warned_at: datetime | None = None

    def revisions_left(self) -> int:
        return max(0, self.revision_limit - self.revisions_used)

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
        # 마감이 새로 잡히므로 임박 알림 표식도 비운다 — 검토 마감에도 한 번 더 알린다(갭 #76)
        return replace(
            self,
            status=OrderStatus.IN_REVIEW,
            deadline_at=now + review_deadline,
            deadline_warned_at=None,
        )

    def ensure_can_attach_deliverable(self, actor_user_id: int) -> None:
        """납품물 등록 검증 — 작업 중(IN_PROGRESS)인 주문의 크리에이터만."""
        self._require_creator(actor_user_id)
        self._require_status(OrderStatus.IN_PROGRESS, "납품물 등록")

    def request_revision(self, actor_user_id: int) -> Order:
        """브랜드 수정 요청 → 재작업. 원 요구사항 범위 내에서 스냅샷된 횟수만큼(§3.3)."""
        self._require_brand(actor_user_id)
        self._require_status(OrderStatus.IN_REVIEW, "수정 요청")
        if self.revisions_left() <= 0:
            raise InvalidOrderTransitionError(
                f"수정 요청은 {self.revision_limit}회까지 가능합니다 (이미 {self.revisions_used}회 사용)."
            )
        return replace(
            self,
            status=OrderStatus.IN_PROGRESS,
            deadline_at=None,
            revisions_used=self.revisions_used + 1,
        )

    def approve(self, actor_user_id: int) -> tuple[Order, list[LedgerEntryDraft]]:
        """브랜드 승인 → 구매 확정: 크리에이터 잔액 적립 + 플랫폼 수수료 확정."""
        self._require_brand(actor_user_id)
        self._require_status(OrderStatus.IN_REVIEW, "승인")
        return self._complete()

    def needs_deadline_warning(self, now: datetime, threshold: timedelta) -> bool:
        """마감 임박 알림 대상인지 — 아직 안 지났고, 임계 안으로 들어왔고, 한 번도 안 보냈을 때.

        무응답 만료는 랭킹 페널티(갭 #32)로 이어지므로 지나기 전에 한 번 알린다.
        """
        if self.deadline_at is None or self.deadline_warned_at is not None:
            return False
        if self.status not in (OrderStatus.PENDING_ACCEPT, OrderStatus.IN_REVIEW):
            return False
        return now < self.deadline_at <= now + threshold

    def deadline_warning_recipient(self) -> int:
        """마감 때문에 움직여야 하는 쪽 — 수락 대기는 크리에이터, 검토 대기는 브랜드."""
        return (
            self.creator_user_id
            if self.status is OrderStatus.PENDING_ACCEPT
            else self.brand_user_id
        )

    def expire(self, now: datetime) -> tuple[Order, list[LedgerEntryDraft]] | None:
        """마감시각 경과 처리(주기 스캔 전용) — 대상 아니면 None.

        PENDING_ACCEPT 만료 → 자동 환불 · IN_REVIEW 만료 → 자동 승인(§3.8).
        """
        if self.deadline_at is None or now < self.deadline_at:
            return None
        if self.status is OrderStatus.PENDING_ACCEPT:
            # 크리에이터 무응답 — 거절 환불과 구분해 표식을 남긴다(랭킹 페널티)
            refunded, entries = self._refund()
            return replace(refunded, accept_expired=True), entries
        if self.status is OrderStatus.IN_REVIEW:
            return self._complete()
        return None

    # ── 진행 중 금액 변경 (§3.8·§6 — 갭 #31) ────────────────────────────

    def _require_adjustable(self, action: str) -> None:
        if self.status not in (OrderStatus.IN_PROGRESS, OrderStatus.IN_REVIEW):
            raise InvalidOrderTransitionError(
                f"{action}은(는) 작업 중·검토 중 상태에서만 가능합니다 (현재: {self.status.value})"
            )

    def ensure_can_request_adjustment(self, actor_user_id: int) -> None:
        """추가 금액 요청 검증 — 진행 중 주문의 크리에이터만."""
        self._require_creator(actor_user_id)
        self._require_adjustable("금액 변경 요청")

    def apply_adjustment(self, extra_amount_krw: int) -> tuple[Order, list[LedgerEntryDraft]]:
        """추가 결제 완료 → 주문 금액 증액 + 늘어난 만큼만 추가 예치 기입.

        수수료율은 주문 시점 스냅샷을 유지하므로 증가분에도 같은 요율이 적용된다.
        """
        self._require_adjustable("금액 변경")
        if extra_amount_krw <= 0:
            raise InvalidOrderTransitionError("추가 금액은 0보다 커야 합니다.")
        increased = replace(self, amount_krw=self.amount_krw + extra_amount_krw)
        entries = [
            LedgerEntryDraft(
                entry_type=LedgerEntryType.ESCROW_DEPOSIT,
                user_id=self.brand_user_id,
                amount_krw=increased.brand_total_krw() - self.brand_total_krw(),
            )
        ]
        return increased, entries

    # ── 양측 합의 취소 (collabstr §3.8 — 갭 #4) ──────────────────────────

    def _require_participant(self, actor_user_id: int) -> None:
        if actor_user_id not in (self.brand_user_id, self.creator_user_id):
            raise NotOrderActorError("주문 당사자만 할 수 있는 동작입니다.")

    def _require_cancellable(self, action: str) -> None:
        if self.status not in (OrderStatus.IN_PROGRESS, OrderStatus.IN_REVIEW):
            raise InvalidOrderTransitionError(
                f"{action}은(는) 작업 중·검토 중 상태에서만 가능합니다 (현재: {self.status.value})"
            )

    def _require_counterpart(self, actor_user_id: int) -> None:
        self._require_participant(actor_user_id)
        if actor_user_id == self.cancel_requested_by:
            raise NotOrderActorError("취소 요청의 상대방만 할 수 있는 동작입니다.")

    def request_cancellation(self, actor_user_id: int) -> Order:
        """당사자 취소 요청 — 상대 동의를 기다린다(주문 상태는 그대로 유지)."""
        self._require_participant(actor_user_id)
        self._require_cancellable("취소 요청")
        if self.cancel_requested_by is not None:
            raise InvalidOrderTransitionError("이미 취소 요청이 대기 중입니다.")
        return replace(self, cancel_requested_by=actor_user_id)

    def consent_cancellation(self, actor_user_id: int) -> tuple[Order, list[LedgerEntryDraft]]:
        """상대방 동의 → 합의 취소 확정: 브랜드에게 전액 환불(크레딧).

        요청자 기록(cancel_requested_by)은 이력으로 보존한다.
        """
        self._require_cancellable("취소 동의")
        if self.cancel_requested_by is None:
            raise InvalidOrderTransitionError("대기 중인 취소 요청이 없습니다.")
        self._require_counterpart(actor_user_id)
        return self._cancel_with_refund()

    def decline_cancellation(self, actor_user_id: int) -> Order:
        """상대방 거부 → 취소 요청 해제, 주문은 계속 진행된다."""
        self._require_cancellable("취소 거부")
        if self.cancel_requested_by is None:
            raise InvalidOrderTransitionError("대기 중인 취소 요청이 없습니다.")
        self._require_counterpart(actor_user_id)
        return replace(self, cancel_requested_by=None)

    # ── 분쟁 중재 (collabstr §3.8 지원팀 중재 — 갭 #4) ────────────────────

    def ensure_can_raise_dispute(self, actor_user_id: int) -> None:
        """분쟁 신고 검증 — 진행 중·검토 중 주문의 당사자만."""
        self._require_participant(actor_user_id)
        self._require_cancellable("분쟁 신고")

    def resolve_dispute_refund(self) -> tuple[Order, list[LedgerEntryDraft]]:
        """운영자 판정: 브랜드 전액 환불(크레딧) — 주문은 취소된다."""
        self._require_cancellable("분쟁 환불 판정")
        return self._cancel_with_refund()

    def resolve_dispute_release(self) -> tuple[Order, list[LedgerEntryDraft]]:
        """운영자 판정: 크리에이터 전액 지급 — 구매 확정과 같은 기입."""
        self._require_cancellable("분쟁 지급 판정")
        return self._complete()

    # ── 전이 결과 (원장 기입과 원자적으로 저장돼야 한다 — BOUNDARIES §1) ──

    def _cancel_with_refund(self) -> tuple[Order, list[LedgerEntryDraft]]:
        cancelled = replace(self, status=OrderStatus.CANCELLED, deadline_at=None)
        entries = [
            LedgerEntryDraft(
                entry_type=LedgerEntryType.BRAND_CREDIT_REFUND,
                user_id=self.brand_user_id,
                amount_krw=self.brand_total_krw(),
            )
        ]
        return cancelled, entries

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
