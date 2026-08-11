from dataclasses import dataclass

# 허용 형식 → 저장 확장자. 영상 납품물까지 받으므로 상한 100MB(채팅 사진 5MB와 다른 용도).
_EXTENSIONS = {
    "image/jpeg": "jpg",
    "image/png": "png",
    "image/webp": "webp",
    "video/mp4": "mp4",
    "video/quicktime": "mov",
    "application/pdf": "pdf",
    "application/zip": "zip",
}
_MAX_BYTES = 100 * 1024 * 1024


@dataclass(frozen=True)
class DeliverableFile:
    """납품물 파일 검증 VO — 형식·크기를 만족해야 생성된다."""

    content: bytes
    content_type: str

    def __post_init__(self) -> None:
        if self.content_type not in _EXTENSIONS:
            allowed = ", ".join(sorted(_EXTENSIONS))
            raise ValueError(f"지원하지 않는 파일 형식입니다: {self.content_type} (허용: {allowed})")
        if len(self.content) == 0:
            raise ValueError("빈 파일은 업로드할 수 없습니다.")
        if len(self.content) > _MAX_BYTES:
            raise ValueError(f"파일은 {_MAX_BYTES // (1024 * 1024)}MB 이하여야 합니다.")

    @property
    def extension(self) -> str:
        return _EXTENSIONS[self.content_type]
