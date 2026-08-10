from dataclasses import dataclass


@dataclass(frozen=True)
class BookkeeperQuery:

    id: int
    name: str


@dataclass(frozen=True)
class BookkeeperResponse:

    id: int
    name: str
    introduction: str
