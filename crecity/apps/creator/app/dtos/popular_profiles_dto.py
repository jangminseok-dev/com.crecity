from dataclasses import dataclass


@dataclass(frozen=True)
class PopularProfilesQuery:

    limit: int  # 카드 수 — 라우터가 상한을 강제한다


# 결과는 profile_listing_dto.ProfileListingItem을 공유한다(같은 카드 형태).
