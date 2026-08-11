from __future__ import annotations

from hub.app.ports.output.campaign_application_port import CampaignApplicationPort

# 조립 지점 — 허브는 스포크를 모르므로 main.py(조립 루트)가 campaign 구현체를 등록한다.
_port: CampaignApplicationPort | None = None


def register_campaign_application_port(port: CampaignApplicationPort) -> None:
    global _port
    _port = port


def get_campaign_application_port() -> CampaignApplicationPort:
    if _port is None:
        raise RuntimeError(
            "CampaignApplicationPort 미등록 — main.py에서 register_campaign_application_port를 "
            "호출해야 합니다."
        )
    return _port
