from pydantic import BaseModel


class HeraldResponseSchema(BaseModel):

    id: int
    name: str
    introduction: str
