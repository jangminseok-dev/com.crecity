from __future__ import annotations

from hub.app.ports.output.dispute_resolution_port import DisputeResolutionPort

# 조립 지점 — 허브는 스포크를 모르므로 main.py(조립 루트)가 order 구현체를 등록한다.
_port: DisputeResolutionPort | None = None


def register_dispute_resolution_port(port: DisputeResolutionPort) -> None:
    global _port
    _port = port


def get_dispute_resolution_port() -> DisputeResolutionPort:
    if _port is None:
        raise RuntimeError(
            "DisputeResolutionPort 미등록 — main.py에서 register_dispute_resolution_port를 호출해야 합니다."
        )
    return _port
