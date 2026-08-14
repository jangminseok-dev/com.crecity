from __future__ import annotations

from hub.app.ports.output.creator_trade_stats_port import CreatorTradeStatsPort

# 조립 지점 — 허브는 스포크를 모르므로 main.py가 order 구현체를 등록한다.
_port: CreatorTradeStatsPort | None = None


def register_creator_trade_stats_port(port: CreatorTradeStatsPort) -> None:
    global _port
    _port = port


def get_creator_trade_stats_port() -> CreatorTradeStatsPort:
    if _port is None:
        raise RuntimeError(
            "CreatorTradeStatsPort 미등록 — main.py에서 register_creator_trade_stats_port를 호출해야 합니다."
        )
    return _port
