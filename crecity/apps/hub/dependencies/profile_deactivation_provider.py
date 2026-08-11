from __future__ import annotations

from hub.app.ports.output.profile_deactivation_port import ProfileDeactivationPort

# 조립 지점 — 허브는 스포크를 모르므로 main.py(조립 루트)가 creator 구현체를 등록한다.
_port: ProfileDeactivationPort | None = None


def register_profile_deactivation_port(port: ProfileDeactivationPort) -> None:
    global _port
    _port = port


def get_profile_deactivation_port() -> ProfileDeactivationPort:
    if _port is None:
        raise RuntimeError(
            "ProfileDeactivationPort 미등록 — main.py에서 register_profile_deactivation_port를 "
            "호출해야 합니다."
        )
    return _port
