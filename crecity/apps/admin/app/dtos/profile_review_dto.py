from dataclasses import dataclass


@dataclass(frozen=True)
class ReviewDecisionCommand:

    profile_id: int
    approved: bool  # True=승인(APPROVED) / False=반려(REJECTED)
    reviewer_id: int  # 감사 기록용 — 누가 심사했는가
    reviewer_email: str
    reason: str | None = None  # 반려 사유(갭 #101) — 반려 시 필수(라우터가 강제)
