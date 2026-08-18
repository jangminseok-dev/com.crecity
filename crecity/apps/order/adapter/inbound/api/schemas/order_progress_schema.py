from pydantic import BaseModel, Field


class RevisionRequestSchema(BaseModel):
    """수정 요청 본문(갭 #84) — 무엇을 고칠지 없는 요청은 재작업이 되지 않는다."""

    comment: str = Field(min_length=5, max_length=2000, description="수정할 내용 피드백")
