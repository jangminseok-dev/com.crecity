from __future__ import annotations

from hub.app.ports.output.completed_order_price_port import CompletedOrderPricePort

# 조립 지점 — 허브는 스포크를 모르므로 main.py(조립 루트)가 order 구현체를 등록한다.
_port: CompletedOrderPricePort | None = None


def register_completed_order_price_port(port: CompletedOrderPricePort) -> None:
    global _port
    _port = port


def get_completed_order_price_port() -> CompletedOrderPricePort:
    if _port is None:
        raise RuntimeError(
            "CompletedOrderPricePort 미등록 — main.py에서 register_completed_order_price_port를 호출해야 합니다."
        )
    return _port
