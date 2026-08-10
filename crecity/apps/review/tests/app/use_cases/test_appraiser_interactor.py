from review.app.dtos.appraiser_dto import AppraiserQuery
from review.app.use_cases.appraiser_interactor import AppraiserInteractor


class _StubRecord:
    def __init__(self):
        self.records = []

    async def record(self, subject, note):
        self.records.append((subject, note))


async def test_자기소개는_실기능_정보를_반환하고_기록을_남긴다():
    record = _StubRecord()
    result = await AppraiserInteractor(record=record).introduce_myself(
        AppraiserQuery(id=7, name="리뷰 (review)")
    )
    assert result.id == 7
    assert result.introduction
    assert record.records[0][0] == "introduce_myself"
