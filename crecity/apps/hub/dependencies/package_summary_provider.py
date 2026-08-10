from __future__ import annotations

from hub.app.ports.output.package_summary_port import PackageSummaryPort

# 조립 지점 — 허브는 스포크를 모르므로 main.py(조립 루트)가 creator 구현체를 등록한다.
_port: PackageSummaryPort | None = None


def register_package_summary_port(port: PackageSummaryPort) -> None:
    global _port
    _port = port


def get_package_summary_port() -> PackageSummaryPort:
    if _port is None:
        raise RuntimeError(
            "PackageSummaryPort 미등록 — main.py에서 register_package_summary_port를 호출해야 합니다."
        )
    return _port
