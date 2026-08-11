from __future__ import annotations

from hub.app.ports.output.withdrawal_settlement_port import WithdrawalSettlementPort

# 조립 지점 — 허브는 스포크를 모르므로 main.py(조립 루트)가 order 구현체를 등록한다.
_port: WithdrawalSettlementPort | None = None


def register_withdrawal_settlement_port(port: WithdrawalSettlementPort) -> None:
    global _port
    _port = port


def get_withdrawal_settlement_port() -> WithdrawalSettlementPort:
    if _port is None:
        raise RuntimeError(
            "WithdrawalSettlementPort 미등록 — main.py에서 register_withdrawal_settlement_port를 호출해야 합니다."
        )
    return _port
