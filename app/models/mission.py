"""Mission and MissionStep models for mission-based learning."""
from sqlalchemy import Boolean, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Mission(Base):
    __tablename__ = "missions"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    title: Mapped[str] = mapped_column(String(255))
    description: Mapped[str] = mapped_column(String(1000), default="")
    purpose: Mapped[str] = mapped_column(String(1000), default="")
    reward_xp: Mapped[int] = mapped_column(Integer, default=100)
    badge: Mapped[str | None] = mapped_column(String(120), nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="not_started")  # not_started | in_progress | completed

    steps: Mapped[list["MissionStep"]] = relationship(
        back_populates="mission", cascade="all, delete-orphan", order_by="MissionStep.order"
    )

    user: Mapped["User"] = relationship(back_populates="missions")  # noqa: F821


class MissionStep(Base):
    __tablename__ = "mission_steps"

    id: Mapped[int] = mapped_column(primary_key=True)
    mission_id: Mapped[int] = mapped_column(ForeignKey("missions.id"), index=True)
    title: Mapped[str] = mapped_column(String(255))
    description: Mapped[str] = mapped_column(String(1000), default="")
    order: Mapped[int] = mapped_column(Integer)
    completed: Mapped[bool] = mapped_column(Boolean, default=False)

    mission: Mapped["Mission"] = relationship(back_populates="steps")