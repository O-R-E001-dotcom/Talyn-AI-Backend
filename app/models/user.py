"""User (learner) model."""
from datetime import datetime

from sqlalchemy import Boolean, DateTime, String, func
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False)
    is_creator: Mapped[bool] = mapped_column(Boolean, default=False)

    # Learner profile fields (mirror LearnerContext)
    learner_name: Mapped[str] = mapped_column(String(120))
    current_course: Mapped[str] = mapped_column(String(255), default="")
    current_lesson: Mapped[str] = mapped_column(String(255), default="")
    current_topic: Mapped[str] = mapped_column(String(255), default="")
    difficulty_level: Mapped[str] = mapped_column(String(20), default="beginner")
    goals: Mapped[str] = mapped_column(String(500), default="")
    interests: Mapped[list[str]] = mapped_column(ARRAY(String), default=list)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    # Relationships
    xp_events: Mapped[list["XpEvent"]] = relationship(back_populates="user")  # noqa: F821
    quiz_results: Mapped[list["QuizResult"]] = relationship(back_populates="user")  # noqa: F821
    enrollments: Mapped[list["Enrollment"]] = relationship(back_populates="user")  # noqa: F821
    lesson_progress: Mapped[list["LessonProgress"]] = relationship(back_populates="user")  # noqa: F821
    badges: Mapped[list["Badge"]] = relationship(back_populates="user")  # noqa: F821
    missions: Mapped[list["Mission"]] = relationship(back_populates="user")  # noqa: F821

    def __repr__(self) -> str:
        return f"<User id={self.id} name={self.learner_name!r}>"