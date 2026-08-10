from chat.app.dtos.courier_dto import CourierQuery
from chat.app.use_cases.courier_interactor import CourierInteractor


class _StubRecord:
    def __init__(self):
        self.records = []

    async def record(self, subject, note):
        self.records.append((subject, note))


async def test_자기소개는_실기능_정보를_반환하고_기록을_남긴다():
    record = _StubRecord()
    result = await CourierInteractor(record=record).introduce_myself(
        CourierQuery(id=9, name="채팅 (chat)")
    )
    assert result.id == 9
    assert result.introduction
    assert record.records[0][0] == "introduce_myself"
