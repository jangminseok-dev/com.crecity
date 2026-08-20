from datetime import datetime

from pydantic import BaseModel, Field

from hub.app.dtos.profile_review_dto import ProfileReviewSummary


class ProfileRejectRequestSchema(BaseModel):
    """반려 요청(갭 #101) — 사유 필수(5~500자): 크리에이터가 보완할 근거가 된다."""

    reason: str = Field(min_length=5, max_length=500)


class ProfileReviewResponseSchema(BaseModel):

    id: int
    slug: str
    name: str
    tagline: str
    bio: str
    primary_category: str
    status: str
    created_at: datetime | None
    # 정량 vetting 자동 체크(갭 #16) — 참고선, 승인·반려 결정은 운영자 몫
    platform_count: int
    total_followers: int
    best_engagement_permille: int | None
    min_followers: int
    min_engagement_permille: int
    vetting_passed: bool

    @classmethod
    def from_summary(cls, summary: ProfileReviewSummary) -> "ProfileReviewResponseSchema":
        return cls(
            id=summary.id,
            slug=summary.slug,
            name=summary.name,
            tagline=summary.tagline,
            bio=summary.bio,
            primary_category=summary.primary_category,
            status=summary.status,
            created_at=summary.created_at,
            platform_count=summary.platform_count,
            total_followers=summary.total_followers,
            best_engagement_permille=summary.best_engagement_permille,
            min_followers=summary.min_followers,
            min_engagement_permille=summary.min_engagement_permille,
            vetting_passed=summary.vetting_passed,
        )
