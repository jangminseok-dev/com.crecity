from __future__ import annotations

from hub.app.ports.output.active_order_port import ActiveOrderPort

# 조립 지점 — 허브는 스포크를 모르므로 main.py(조립 루트)가 order 구현체를 등록한다.
_port: ActiveOrderPort | None = None


def register_active_order_port(port: ActiveOrderPort) -> None:
    global _port
    _port = port


def get_active_order_port() -> ActiveOrderPort:
    if _port is None:
        raise RuntimeError(
            "ActiveOrderPort 미등록 — main.py에서 register_active_order_port를 호출해야 합니다."
        )
    return _port
