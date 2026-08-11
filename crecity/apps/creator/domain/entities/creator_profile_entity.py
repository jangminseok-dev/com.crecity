from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum


class ProfileStatus(StrEnum):
    """프로필 심사 상태 — 등록 즉시 PENDING, 심사(admin)로 APPROVED/REJECTED 전이.

    REJECTED여도 슬러그 직접 조회는 가능하고 마켓플레이스 목록에서만 제외된다
    (collabstr-analysis §3.8 온보딩 정책).
    """

    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    DELETED = "DELETED"  # 계정 삭제로 비활성화(§3.8, 갭 #33) — 공개 조회도 막힌다


@dataclass(frozen=True, slots=True)
class CreatorProfile:
    """크리에이터 프로필 도메인 엔티티 — ORM/프레임워크에 의존하지 않는다."""

    id: int
    slug: str
    name: str
    tagline: str  # 한 줄 포지셔닝 (collabstr §2.1 헤더)
    bio: str
    location: str | None
    primary_category: str  # 니치 카테고리 — 다중 카테고리는 M:N 필요 시점에 정규화
    status: ProfileStatus
    # 소유 계정(auth users 논리 참조) — None은 소셜 로그인 도입 전 레거시 행뿐
    user_id: int | None = None
    created_at: datetime | None = None

    def is_listable(self) -> bool:
        """마켓플레이스 목록 노출 가능 여부 — 승인된 프로필만."""
        return self.status is ProfileStatus.APPROVED

    def is_owned_by(self, user_id: int) -> bool:
        """쓰기 권한 판정 — 소유자 본인만 수정·삭제할 수 있다."""
        return self.user_id is not None and self.user_id == user_id
