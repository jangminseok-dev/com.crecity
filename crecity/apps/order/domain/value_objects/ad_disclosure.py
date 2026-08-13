import re

# 공정위 「추천·보증 등에 관한 표시·광고 심사지침」이 인정하는 대가성 표시 문구들.
# 오탐보다 미탐이 위험하므로 넓게 잡되, 영어 "ad"는 해시태그 형태만 본다(advance 등 오탐 차단).
_PATTERN = re.compile(
    r"광고|협찬|ppl|피피엘|대가|제공\s*받|지원\s*받|sponsored|paid\s*partnership|#ad\b",
    re.IGNORECASE,
)


def has_ad_disclosure(text: str | None) -> bool:
    """게시물 본문에 광고·협찬 표기가 있는지 — 없으면 경고 대상(제출·승인을 막지는 않는다)."""
    return bool(text and _PATTERN.search(text))
