from datetime import datetime
from typing import Dict, Optional

from pydantic import BaseModel, Field

from app.models.user import UsersResponse


class UserPlanMeta(BaseModel):
    plan_id: int = Field(gt=0)
    plan_name: str
    version_id: int = Field(gt=0)
    version_number: int = Field(gt=0)
    is_trial: bool = False
    operation_type: str
    assigned_at: datetime


class UsersManagementResponse(UsersResponse):
    plan_meta: Dict[str, Optional[UserPlanMeta]] = Field(default_factory=dict)
