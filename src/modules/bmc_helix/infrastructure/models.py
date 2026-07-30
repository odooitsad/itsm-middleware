from datetime import datetime

from sqlalchemy import JSON, DateTime, Index, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from src.core.database.base import Base


class TransactionModel(Base):
    __tablename__ = "bmc_helix_transactions"
    __table_args__ = (Index("idx_service_code", "service_code"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now(), nullable=False
    )
    service_code: Mapped[str | None] = mapped_column(String(100), nullable=True)
    event_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    status: Mapped[str] = mapped_column(String(100), nullable=False)
    incident_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    request: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    response: Mapped[dict | None] = mapped_column(JSON, nullable=True)


class ProductCategorizationModel(Base):
    __tablename__ = "bmc_helix_product_categorizations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    product_categorization_tier_1: Mapped[str] = mapped_column(String(200))
    product_categorization_tier_2: Mapped[str] = mapped_column(String(200))
    product_categorization_tier_3: Mapped[str] = mapped_column(String(200))
    product_name: Mapped[str] = mapped_column(String(200))


class OperationalCategorizationModel(Base):
    __tablename__ = "bmc_helix_operational_categorizations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    categorization_tier_1: Mapped[str] = mapped_column(String(200))
    categorization_tier_2: Mapped[str] = mapped_column(String(200))
    categorization_tier_3: Mapped[str] = mapped_column(String(200))
    title: Mapped[str] = mapped_column(String(300))
    assigned_group: Mapped[str] = mapped_column(String(100))
    assignee: Mapped[str] = mapped_column(String(200))
    description: Mapped[str] = mapped_column(String(5000))
