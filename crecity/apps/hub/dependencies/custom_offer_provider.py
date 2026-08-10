from __future__ import annotations

from hub.app.ports.output.custom_offer_port import CustomOfferPort

# 조립 지점 — 허브는 스포크를 모르므로 main.py(조립 루트)가 chat 구현체를 등록한다.
_port: CustomOfferPort | None = None


def register_custom_offer_port(port: CustomOfferPort) -> None:
    global _port
    _port = port


def get_custom_offer_port() -> CustomOfferPort:
    if _port is None:
        raise RuntimeError(
            "CustomOfferPort 미등록 — main.py에서 register_custom_offer_port를 호출해야 합니다."
        )
    return _port
