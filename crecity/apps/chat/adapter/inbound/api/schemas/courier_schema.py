from pydantic import BaseModel


class CourierResponseSchema(BaseModel):

    id: int
    name: str
    introduction: str
