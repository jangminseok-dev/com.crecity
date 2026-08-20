from dataclasses import dataclass

# 고정 카테고리 목록 (2026-08-11 확정 · 2026-08-20 국내 강세 세분화 갭 #100) —
# 탐색 필터·아이콘 세트·www CREATOR_CATEGORIES와 1:1. 제거·개명은 기존 프로필을
# 깨뜨리므로 하지 않는다(추가만).
CATEGORIES: tuple[str, ...] = (
    "뷰티",
    "패션",
    "푸드",
    "여행",
    "테크",
    "피트니스",
    "라이프",
    "포토",
    "영상",
    # 국내 강세 세분화(갭 #100, collabstr §1 니치 26개·§9.2)
    "육아",
    "반려동물",
    "게임",
    "교육",
    "리빙",
    "아웃도어",
    "비즈니스",
    "음악",
    "엔터테인먼트",
)


@dataclass(frozen=True)
class Category:
    """프로필 카테고리 VO — 고정 목록에 있어야 생성된다."""

    value: str

    def __post_init__(self) -> None:
        if self.value not in CATEGORIES:
            allowed = ", ".join(CATEGORIES)
            raise ValueError(f"지원하지 않는 카테고리입니다: {self.value} (허용: {allowed})")
