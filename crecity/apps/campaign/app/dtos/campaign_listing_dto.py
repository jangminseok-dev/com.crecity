from dataclasses import dataclass


@dataclass(frozen=True)
class OpenCampaignsQuery:

    limit: int
    offset: int


@dataclass(frozen=True)
class CampaignDetailQuery:

    campaign_id: int
