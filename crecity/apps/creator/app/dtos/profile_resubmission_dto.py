from dataclasses import dataclass


@dataclass(frozen=True)
class ProfileResubmissionCommand:
    """반려 프로필의 재심사 요청(갭 #101) — 본인·REJECTED 상태에서만."""

    user_id: int
