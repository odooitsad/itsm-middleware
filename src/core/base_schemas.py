from enum import StrEnum

from pydantic import BaseModel, Field


class ZabbixEventUrgency(StrEnum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class ZabbixBase(BaseModel):
    description: str = Field(
        examples=["Pruebas DEV"],
        max_length=10000,
    )
    end_date: str | None = Field(
        None,
        examples=["2026.02.18T20:31:24"],
        max_length=50,
    )
    event_id: str = Field(
        examples=["123456789"],
        max_length=50,
    )
    event_value: str = Field(
        examples=["1"],
        description="Value that defines start(1) or end(0) of the event",
        max_length=1,
    )
    host_id: int = Field(
        examples=[10711],
    )
    host_name: str = Field(
        examples=["GRH0931_BOGSO_vEdge1"],
        max_length=100,
    )
    start_date: str = Field(
        examples=["2026.02.18T20:31:24"],
        max_length=50,
    )
    title: str = Field(
        examples=["DATASMART//GRH0931//memoria//supero 70%"],
        max_length=100,
    )
    urgency: ZabbixEventUrgency = ZabbixEventUrgency.LOW
