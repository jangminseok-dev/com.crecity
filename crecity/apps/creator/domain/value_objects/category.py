from dataclasses import dataclass

# 고정 카테고리 목록 (2026-08-11 확정) — 탐색 필터·아이콘 세트와 1:1.
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
)


@dataclass(frozen=True)
class Category:
    """프로필 카테고리 VO — 고정 목록에 있어야 생성된다."""

    value: str

    def __post_init__(self) -> None:
        if self.value not in CATEGORIES:
            allowed = ", ".join(CATEGORIES)
            raise ValueError(f"지원하지 않는 카테고리입니다: {self.value} (허용: {allowed})")
