from dataclasses import dataclass

# 허용 이미지 형식 → 저장 확장자. 업로드 상한 5MB — 채팅 사진 용도.
# (creator의 ImageFile과 동일 규격 — 스포크 독립 원칙상 공유하지 않고 각자 소유한다)
_EXTENSIONS = {"image/jpeg": "jpg", "image/png": "png", "image/webp": "webp"}
_MAX_BYTES = 5 * 1024 * 1024


@dataclass(frozen=True)
class ImageFile:
    """업로드 이미지 검증 VO — 형식·크기를 만족해야 생성된다."""

    content: bytes
    content_type: str

    def __post_init__(self) -> None:
        if self.content_type not in _EXTENSIONS:
            allowed = ", ".join(sorted(_EXTENSIONS))
            raise ValueError(f"지원하지 않는 이미지 형식입니다: {self.content_type} (허용: {allowed})")
        if len(self.content) == 0:
            raise ValueError("빈 파일은 업로드할 수 없습니다.")
        if len(self.content) > _MAX_BYTES:
            raise ValueError(f"이미지는 {_MAX_BYTES // (1024 * 1024)}MB 이하여야 합니다.")

    @property
    def extension(self) -> str:
        return _EXTENSIONS[self.content_type]
