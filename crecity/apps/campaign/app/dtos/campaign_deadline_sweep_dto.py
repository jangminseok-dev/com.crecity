from dataclasses import dataclass


@dataclass(frozen=True)
class CampaignSweepResult:
    """마감일 경과로 자동 마감된 공고 id 목록."""

    closed_campaign_ids: list[int]
