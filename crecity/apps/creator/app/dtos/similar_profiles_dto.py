from dataclasses import dataclass


@dataclass(frozen=True)
class SimilarProfilesQuery:

    slug: str  # 기준 프로필 — 이 프로필과 비슷한 크리에이터를 찾는다
    limit: int  # 카드 수 — 라우터가 상한을 강제한다


# 결과는 profile_listing_dto.ProfileListingItem을 공유한다(같은 카드 형태 — popular와 동일).
