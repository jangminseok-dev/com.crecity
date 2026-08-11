from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class CancellationCommand:
    order_id: int
    actor_user_id: int
