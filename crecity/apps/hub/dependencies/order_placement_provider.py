from __future__ import annotations

from hub.app.ports.output.order_placement_port import OrderPlacementPort

# 조립 지점 — 허브는 스포크를 모르므로 main.py(조립 루트)가 order 구현체를 등록한다.
_port: OrderPlacementPort | None = None


def register_order_placement_port(port: OrderPlacementPort) -> None:
    global _port
    _port = port


def get_order_placement_port() -> OrderPlacementPort:
    if _port is None:
        raise RuntimeError(
            "OrderPlacementPort 미등록 — main.py에서 register_order_placement_port를 호출해야 합니다."
        )
    return _port
