from dataclasses import dataclass


@dataclass(frozen=True)
class ClearFlagCommand:
    """이상치 플래그 확인 처리 커맨드(갭 #82) — 감사 기록용 처리자 정보 포함."""

    analytics_id: int
    reviewer_id: int
    reviewer_email: str
