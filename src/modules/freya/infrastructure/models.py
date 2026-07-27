from datetime import datetime

from sqlalchemy import JSON, DateTime, Integer, SmallInteger, String, func
from sqlalchemy.orm import Mapped, mapped_column

from src.core.database.base import Base


class TransactionModel(Base):
    __tablename__ = "freya_transaction_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )
    service_code: Mapped[str] = mapped_column(String(100))
    event_id: Mapped[str] = mapped_column(String(100))
    im_id: Mapped[str | None] = mapped_column(String(100))
    status: Mapped[str] = mapped_column(
        String(100), nullable=False, default="En proceso"
    )
    status_im: Mapped[int] = mapped_column(SmallInteger, nullable=False, default=-1)
    hostid: Mapped[int | None] = mapped_column(Integer)
    request: Mapped[dict] = mapped_column(JSON)
    response: Mapped[dict | None] = mapped_column(JSON)
