from __future__ import annotations

from typing import Optional

from sqlalchemy import CheckConstraint, Column, Float, ForeignKey, Integer, String, Table, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from src.db.base import Base

organization_activity = Table(
    "organization_activity",
    Base.metadata,
    Column("organization_id", ForeignKey("organizations.id", ondelete="CASCADE"), primary_key=True),
    Column("activity_id", ForeignKey("activities.id", ondelete="CASCADE"), primary_key=True),
    UniqueConstraint("organization_id", "activity_id", name="uq_org_activity"),
)


class Building(Base):
    __tablename__ = "buildings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    address: Mapped[str] = mapped_column(String(500), nullable=False)
    latitude: Mapped[float] = mapped_column(Float, nullable=False)
    longitude: Mapped[float] = mapped_column(Float, nullable=False)

    organizations: Mapped[list[Organization]] = relationship(back_populates="building")


class Activity(Base):
    __tablename__ = "activities"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)

    parent_id: Mapped[Optional[int]] = mapped_column(ForeignKey("activities.id", ondelete="SET NULL"), nullable=True)
    parent: Mapped[Optional[Activity]] = relationship(remote_side=[id], back_populates="children")
    children: Mapped[list[Activity]] = relationship(back_populates="parent")

    organizations: Mapped[list[Organization]] = relationship(
        secondary=organization_activity,
        back_populates="activities",
    )

    __table_args__ = (UniqueConstraint("parent_id", "name", name="uq_activity_parent_name"),)


class Organization(Base):
    __tablename__ = "organizations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(300), nullable=False)

    building_id: Mapped[int] = mapped_column(ForeignKey("buildings.id", ondelete="RESTRICT"), nullable=False)
    building: Mapped[Building] = relationship(back_populates="organizations")

    phones: Mapped[list[OrganizationPhone]] = relationship(
        back_populates="organization",
        cascade="all, delete-orphan",
    )

    activities: Mapped[list[Activity]] = relationship(
        secondary=organization_activity,
        back_populates="organizations",
    )


class OrganizationPhone(Base):
    __tablename__ = "organization_phones"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    organization_id: Mapped[int] = mapped_column(ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    phone: Mapped[str] = mapped_column(String(32), nullable=False)

    organization: Mapped[Organization] = relationship(back_populates="phones")

    __table_args__ = (
        CheckConstraint("length(phone) >= 10", name="ck_phone_min_len"),
        CheckConstraint("length(phone) <= 11", name="ck_phone_max_len"),
    )