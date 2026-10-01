"""Mission and buddy-match schemas."""
from pydantic import BaseModel, Field


# ── Missions ──────────────────────────────────────────────────────────────────

class MissionStepCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    description: str = Field(default="", max_length=1000)
    order: int = Field(..., ge=1)


class MissionCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    description: str = Field(default="", max_length=1000)
    purpose: str = Field(default="", max_length=1000)
    reward_xp: int = Field(default=100, ge=0, le=1000)
    badge: str | None = Field(default=None, max_length=120)
    steps: list[MissionStepCreate] = Field(default_factory=list)


class MissionStepRead(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    title: str
    description: str
    order: int
    completed: bool


class MissionRead(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    title: str
    description: str
    purpose: str
    reward_xp: int
    badge: str | None
    status: str
    steps: list[MissionStepRead] = []


class MissionStatusUpdate(BaseModel):
    status: str = Field(..., min_length=1, max_length=20)


MISSION_STATUSES = {"not_started", "in_progress", "completed"}


# ── Buddy matches ─────────────────────────────────────────────────────────────

class BuddyMatchCreate(BaseModel):
    buddy_user_id: int = Field(..., ge=1)
    match_score: int = Field(default=0, ge=0, le=100)


class BuddyMatchRead(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    buddy_user_id: int
    match_score: int
    status: str


class BuddyMatchStatusUpdate(BaseModel):
    status: str = Field(..., min_length=1, max_length=20)


BUDDY_MATCH_STATUSES = {"pending", "accepted", "declined"}
