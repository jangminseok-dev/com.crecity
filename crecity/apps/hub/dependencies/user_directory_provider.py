from __future__ import annotations

from hub.app.ports.output.user_directory_port import UserDirectoryPort

# 조립 지점 — 허브는 스포크를 모르므로 main.py(조립 루트)가 auth 구현체를 등록한다.
_port: UserDirectoryPort | None = None


def register_user_directory_port(port: UserDirectoryPort) -> None:
    global _port
    _port = port


def get_user_directory_port() -> UserDirectoryPort:
    if _port is None:
        raise RuntimeError(
            "UserDirectoryPort 미등록 — main.py에서 register_user_directory_port를 호출해야 합니다."
        )
    return _port
