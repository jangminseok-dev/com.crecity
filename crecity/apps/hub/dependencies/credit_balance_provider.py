from __future__ import annotations

from hub.app.ports.output.credit_balance_port import CreditBalancePort

# 조립 지점 — 허브는 스포크를 모르므로 main.py(조립 루트)가 order 구현체를 등록한다.
_port: CreditBalancePort | None = None


def register_credit_balance_port(port: CreditBalancePort) -> None:
    global _port
    _port = port


def get_credit_balance_port() -> CreditBalancePort:
    if _port is None:
        raise RuntimeError(
            "CreditBalancePort 미등록 — main.py에서 register_credit_balance_port를 호출해야 합니다."
        )
    return _port
