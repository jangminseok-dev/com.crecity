from order.app.dtos.bookkeeper_dto import BookkeeperQuery
from order.app.use_cases.bookkeeper_interactor import BookkeeperInteractor


class _StubRecord:
    def __init__(self):
        self.records = []

    async def record(self, subject, note):
        self.records.append((subject, note))


async def test_자기소개는_실기능_정보를_반환하고_기록을_남긴다():
    record = _StubRecord()
    result = await BookkeeperInteractor(record=record).introduce_myself(
        BookkeeperQuery(id=4, name="주문 (order)")
    )
    assert result.id == 4
    assert result.introduction
    assert record.records[0][0] == "introduce_myself"
