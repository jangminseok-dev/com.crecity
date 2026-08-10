from __future__ import annotations

from hub.app.ports.output.creator_ref_port import CreatorRefPort

# 조립 지점 — 허브는 스포크를 모르므로 main.py(조립 루트)가 creator 구현체를 등록한다.
_port: CreatorRefPort | None = None


def register_creator_ref_port(port: CreatorRefPort) -> None:
    global _port
    _port = port


def get_creator_ref_port() -> CreatorRefPort:
    if _port is None:
        raise RuntimeError(
            "CreatorRefPort 미등록 — main.py에서 register_creator_ref_port를 호출해야 합니다."
        )
    return _port
