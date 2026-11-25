from enum import Enum
from pydantic import BaseModel, ConfigDict, Field


class Decision(str, Enum):
    ALLOW = "ALLOW"
    HOLD = "HOLD"
    DENY = "DENY"


class Operation(BaseModel):
    model_config = ConfigDict(extra="forbid")
    device_id: str = Field(min_length=1, max_length=80)
    action: str = Field(min_length=1, max_length=80)
    parameters: dict[str, str | float | int | bool | None]
    duration_seconds: int = Field(gt=0, le=86400)
    chemicals: list[str] = Field(default_factory=list)
    description: str = Field(default="", max_length=2000)


class Evaluation(BaseModel):
    decision: Decision
    reasons: list[str]
    simulation_only: bool = True
    execution_id: str | None = None


class SimulateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    operation: Operation
    approval_token: str | None = None
