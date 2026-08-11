from __future__ import annotations

from hub.app.ports.output.creator_popularity_port import CreatorPopularityPort

# 조립 지점 — 허브는 스포크를 모르므로 main.py(조립 루트)가 order 구현체를 등록한다.
_port: CreatorPopularityPort | None = None


def register_creator_popularity_port(port: CreatorPopularityPort) -> None:
    global _port
    _port = port


def get_creator_popularity_port() -> CreatorPopularityPort:
    if _port is None:
        raise RuntimeError(
            "CreatorPopularityPort 미등록 — main.py에서 register_creator_popularity_port를 호출해야 합니다."
        )
    return _port
