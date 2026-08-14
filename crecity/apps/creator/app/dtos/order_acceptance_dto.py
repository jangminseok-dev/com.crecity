from dataclasses import dataclass


@dataclass(frozen=True)
class OrderAcceptanceCommand:

    user_id: int
    accepting: bool


@dataclass(frozen=True)
class OrderAcceptanceResult:

    slug: str
    accepting_orders: bool
