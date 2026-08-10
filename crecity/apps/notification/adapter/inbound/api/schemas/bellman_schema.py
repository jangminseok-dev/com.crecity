from pydantic import BaseModel


class BellmanResponseSchema(BaseModel):

    id: int
    name: str
    introduction: str
