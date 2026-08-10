from dataclasses import dataclass


@dataclass(frozen=True)
class UserRef:
    """회원 참조 요약 — chat 상대 표시 등 소비(BOUNDARIES §5 회원 디렉토리 조회)."""

    user_id: int
    name: str
    account_type: str
