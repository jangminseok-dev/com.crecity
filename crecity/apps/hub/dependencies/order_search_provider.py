from __future__ import annotations

from hub.app.ports.output.order_search_port import OrderSearchPort

# 조립 지점 — 허브는 스포크를 모르므로 main.py가 order 구현체를 등록한다.
_port: OrderSearchPort | None = None


def register_order_search_port(port: OrderSearchPort) -> None:
    global _port
    _port = port


def get_order_search_port() -> OrderSearchPort:
    if _port is None:
        raise RuntimeError(
            "OrderSearchPort 미등록 — main.py에서 register_order_search_port를 호출해야 합니다."
        )
    return _port
