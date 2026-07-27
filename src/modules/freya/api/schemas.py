from datetime import datetime
from typing import Annotated, Literal

from pydantic import AfterValidator, BaseModel, Field, field_validator

from src.modules.freya.domain.entities import CloseIMInput, CreateIMInput, UpdateIMInput


def _clean_list_field(value: str | list[str]) -> list[str]:
    """Split text into <=1000-char chunks, as required by the Freya API."""
    if isinstance(value, str):
        value = [value]

    chunks: list[str] = []
    for item in value:
        for i in range(0, len(item), 1000):
            chunks.append(item[i : i + 1000])
    return chunks


def _im_must_start_with_im(value: str) -> str:
    if not value.startswith("IM"):
        raise ValueError("value must start with 'IM'")
    return value


# Path-parameter type for routes identifying an IM by its id (e.g. /{incident_id}/...).
ImId = Annotated[str, AfterValidator(_im_must_start_with_im)]


class CreateIMRequest(BaseModel):
    affected_ci: str = Field(examples=["GRH3658"], description="Affected service code")
    area: str = Field("No Hay Navegación", examples=["Conectividad Limitada"])
    category: str = Field("incident")
    ci_is_operational: bool = Field(True)
    description: str | list[str] = Field(examples=["Pruebas DEV"])
    impact: Literal["1", "2", "3"] = Field(
        description="Impact levels: '1' - High, '2' - Medium, '3' - Low"
    )
    init_service: str = Field(
        description="ISO 8601 date: %Y-%m-%dT%H:%M:%S%z",
        examples=["2026-07-20T16:13:53-05:00"],
    )
    origin: str = Field("3", description="3: event created from SM")
    sub_category: str = Field("failure")
    title: str = Field(
        max_length=150, examples=["DATASMART//GRH3658//memoria//supero 70%"]
    )
    urgency: Literal["1", "2", "3"] = Field(
        description="Urgency levels: '1' - High, '2' - Medium, '3' - Low"
    )

    @field_validator("description")
    @classmethod
    def validate_description(cls, v: str | list[str]) -> list[str]:
        return _clean_list_field(v)

    def to_input(self) -> CreateIMInput:
        return CreateIMInput(
            area=self.area,
            affected_ci=self.affected_ci,
            category=self.category,
            ci_is_operational=self.ci_is_operational,
            description=self.description,  # type: ignore[arg-type]
            event_id="1",
            impact=self.impact,
            init_service=self.init_service,
            origin=self.origin,
            sub_category=self.sub_category,
            title=self.title,
            urgency=self.urgency,
        )


class UpdateIMRequest(BaseModel):
    working_note: str | list[str] = Field(examples=["Pruebas DEV 1"])
    type: Literal["TROUBLESHOOTING", "SERVICIO OPERATIVO"]

    @field_validator("working_note")
    @classmethod
    def validate_working_note(cls, v: str | list[str]) -> list[str]:
        return _clean_list_field(v)

    def to_input(self, incident_id: str) -> UpdateIMInput:
        return UpdateIMInput(
            existing_im=incident_id,
            working_note=self.working_note,  # type: ignore[arg-type]
            type=self.type,
        )


class CloseIMRequest(BaseModel):
    service_end_date: str = Field(
        description="ISO 8601 date: %Y-%m-%dT%H:%M:%S%z",
        examples=["2026-07-21T16:23:53-05:00"],
    )

    @field_validator("service_end_date")
    @classmethod
    def validate_service_end_date(cls, v: str) -> str:
        s = v[:-1] + "+00:00" if v.endswith("Z") else v
        try:
            dt = datetime.fromisoformat(s)
        except ValueError as exc:
            raise ValueError(
                "service_end_date must be a valid ISO 8601 string "
                "(e.g. 2025-10-15T16:23:53-05:00 or 2025-10-15T21:23:53Z)"
            ) from exc
        if dt.tzinfo is None:
            raise ValueError(
                "service_end_date must include a timezone offset (e.g. -05:00 or Z)"
            )
        return dt.isoformat()

    def to_input(self, incident_id: str) -> CloseIMInput:
        return CloseIMInput(im_id=incident_id, service_end_date=self.service_end_date)


class IMResponse(BaseModel):
    detail: str
    im: str | None = Field(None, serialization_alias="incident_id")
