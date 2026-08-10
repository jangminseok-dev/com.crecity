from dataclasses import dataclass


@dataclass(frozen=True)
class ProfileQuery:

    id: int
    name: str


@dataclass(frozen=True)
class ProfileResponse:

    id: int
    name: str
    introduction: str
