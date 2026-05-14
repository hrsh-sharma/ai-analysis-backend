import uuid
from datetime import datetime
from sqlalchemy import String, Integer, ForeignKey, DateTime, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from core.database import Base


def generate_id() -> str:
    return str(uuid.uuid4())[:8]


class Report(Base):
    __tablename__ = "reports"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=generate_id)
    url: Mapped[str] = mapped_column(String, nullable=False)
    screenshot_url: Mapped[str | None] = mapped_column(String, nullable=True)
    overall_score: Mapped[int] = mapped_column(Integer, default=0)
    overall_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String, default="pending")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    categories: Mapped[list["Category"]] = relationship(
        back_populates="report",
        cascade="all, delete-orphan",
    )


class Category(Base):
    __tablename__ = "categories"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=generate_id)
    report_id: Mapped[str] = mapped_column(ForeignKey("reports.id"))
    name: Mapped[str] = mapped_column(String)
    score: Mapped[int] = mapped_column(Integer)
    summary: Mapped[str] = mapped_column(Text)

    report: Mapped["Report"] = relationship(back_populates="categories")
    issues: Mapped[list["Issue"]] = relationship(
        back_populates="category",
        cascade="all, delete-orphan",
    )
    good_points: Mapped[list["GoodPoint"]] = relationship(
        back_populates="category",
        cascade="all, delete-orphan",
    )


class Issue(Base):
    __tablename__ = "issues"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=generate_id)
    category_id: Mapped[str] = mapped_column(ForeignKey("categories.id"))
    severity: Mapped[str] = mapped_column(String)
    title: Mapped[str] = mapped_column(String)
    description: Mapped[str] = mapped_column(Text)
    how_to_fix: Mapped[str] = mapped_column(Text)

    category: Mapped["Category"] = relationship(back_populates="issues")


class GoodPoint(Base):
    __tablename__ = "good_points"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=generate_id)
    category_id: Mapped[str] = mapped_column(ForeignKey("categories.id"))
    text: Mapped[str] = mapped_column(Text)

    category: Mapped["Category"] = relationship(back_populates="good_points")
