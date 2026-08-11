from dataclasses import dataclass

_MAX_LENGTH = 1000


@dataclass(frozen=True)
class DeliverableLink:
    """납품물 링크 검증 VO — http(s) URL만 허용한다."""

    url: str

    def __post_init__(self) -> None:
        if not self.url.startswith(("http://", "https://")):
            raise ValueError("링크는 http:// 또는 https:// 로 시작해야 합니다.")
        if len(self.url) > _MAX_LENGTH:
            raise ValueError(f"링크는 {_MAX_LENGTH}자 이하여야 합니다.")
