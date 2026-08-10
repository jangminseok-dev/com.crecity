from __future__ import annotations

from hub.app.ports.output.profile_review_port import ProfileReviewPort

# 조립 지점 — 허브는 스포크를 모르므로 main.py(조립 루트)가 creator 구현체를 등록한다.
_port: ProfileReviewPort | None = None


def register_profile_review_port(port: ProfileReviewPort) -> None:
    global _port
    _port = port


def get_profile_review_port() -> ProfileReviewPort:
    if _port is None:
        raise RuntimeError(
            "ProfileReviewPort 미등록 — main.py에서 register_profile_review_port를 호출해야 합니다."
        )
    return _port
