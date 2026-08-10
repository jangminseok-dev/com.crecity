from dataclasses import dataclass


@dataclass(frozen=True)
class BellmanQuery:

    id: int
    name: str


@dataclass(frozen=True)
class BellmanResponse:

    id: int
    name: str
    introduction: str
