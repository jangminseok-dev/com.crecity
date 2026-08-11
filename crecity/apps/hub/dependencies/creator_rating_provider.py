from __future__ import annotations

from hub.app.ports.output.creator_rating_port import CreatorRatingPort

# 조립 지점 — 허브는 스포크를 모르므로 main.py(조립 루트)가 review 구현체를 등록한다.
_port: CreatorRatingPort | None = None


def register_creator_rating_port(port: CreatorRatingPort) -> None:
    global _port
    _port = port


def get_creator_rating_port() -> CreatorRatingPort:
    if _port is None:
        raise RuntimeError(
            "CreatorRatingPort 미등록 — main.py에서 register_creator_rating_port를 호출해야 합니다."
        )
    return _port
