from pydantic import BaseModel


class StewardResponseSchema(BaseModel):

    id: int
    name: str
    introduction: str
