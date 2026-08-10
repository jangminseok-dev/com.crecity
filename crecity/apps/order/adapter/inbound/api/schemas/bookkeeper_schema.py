from pydantic import BaseModel


class BookkeeperResponseSchema(BaseModel):

    id: int
    name: str
    introduction: str
