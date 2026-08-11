from __future__ import annotations

from hub.app.ports.output.order_adjustment_port import OrderAdjustmentPort

# 조립 지점 — 허브는 스포크를 모르므로 main.py(조립 루트)가 order 구현체를 등록한다.
_port: OrderAdjustmentPort | None = None


def register_order_adjustment_port(port: OrderAdjustmentPort) -> None:
    global _port
    _port = port


def get_order_adjustment_port() -> OrderAdjustmentPort:
    if _port is None:
        raise RuntimeError(
            "OrderAdjustmentPort 미등록 — main.py에서 register_order_adjustment_port를 "
            "호출해야 합니다."
        )
    return _port
