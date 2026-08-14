from __future__ import annotations

from hub.app.ports.output.platform_metrics_port import (
    AccountMetricsPort,
    OrderMetricsPort,
    ProfileMetricsPort,
)

# 조립 지점 — 허브는 스포크를 모르므로 main.py가 auth·creator·order 구현체를 등록한다.
_account_port: AccountMetricsPort | None = None
_profile_port: ProfileMetricsPort | None = None
_order_port: OrderMetricsPort | None = None


def register_account_metrics_port(port: AccountMetricsPort) -> None:
    global _account_port
    _account_port = port


def register_profile_metrics_port(port: ProfileMetricsPort) -> None:
    global _profile_port
    _profile_port = port


def register_order_metrics_port(port: OrderMetricsPort) -> None:
    global _order_port
    _order_port = port


def get_account_metrics_port() -> AccountMetricsPort:
    if _account_port is None:
        raise RuntimeError(
            "AccountMetricsPort 미등록 — main.py에서 register_account_metrics_port를 호출해야 합니다."
        )
    return _account_port


def get_profile_metrics_port() -> ProfileMetricsPort:
    if _profile_port is None:
        raise RuntimeError(
            "ProfileMetricsPort 미등록 — main.py에서 register_profile_metrics_port를 호출해야 합니다."
        )
    return _profile_port


def get_order_metrics_port() -> OrderMetricsPort:
    if _order_port is None:
        raise RuntimeError(
            "OrderMetricsPort 미등록 — main.py에서 register_order_metrics_port를 호출해야 합니다."
        )
    return _order_port
