class DuplicateSlugError(Exception):
    """이미 사용 중인 슬러그로 등록 시도 — 라우터에서 409로 변환."""


class ProfileNotFoundError(Exception):
    """슬러그에 해당하는 프로필 없음 — 라우터에서 404로 변환."""
