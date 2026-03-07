from dataclasses import dataclass, field
from datetime import datetime
from typing import Literal
from uuid import UUID, uuid4

TenantPlan = Literal["free", "pro", "enterprise"]
PLAN_LIMITS: dict[str, int] = {"free": 5, "pro": 50, "enterprise": 1000}

@dataclass
class Tenant:
    name: str
    slug: str
    owner_email: str
    id: UUID = field(default_factory=uuid4)
    plan: TenantPlan = "free"
    is_active: bool = True
    max_members: int = 5
    member_count: int = 0
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

    def can_add_member(self) -> bool:
        return self.member_count < self.max_members

    def upgrade_plan(self, new_plan: TenantPlan) -> None:
        self.plan = new_plan
        self.max_members = PLAN_LIMITS[new_plan]
        self.updated_at = datetime.utcnow()
