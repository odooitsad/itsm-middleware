from typing import Literal

from pydantic import BaseModel, Field

from src.bmc_helix.domain.entities import CreateIncidentInput


class CreateIncidentRequest(BaseModel):
    assigned_group: str = Field(
        serialization_alias="Assigned Group",
        examples=["Sop_Telco"],
    )
    assigned_support_company: str = Field(
        serialization_alias="Assigned Support Company",
        examples=["CENIT"],
    )
    assigned_support_organization: str = Field(
        serialization_alias="Assigned Support Organization",
        examples=["Soporte Tecnico"],
    )
    assignee: str = Field(
        serialization_alias="Assignee",
        examples=["Jesus Alberto de La Hoz Jimenez"],
    )
    categorization_tier_1: str = Field(
        serialization_alias="Categorization Tier 1",
        examples=["Redes y telecomunicaciones"],
    )
    categorization_tier_2: str = Field(
        serialization_alias="Categorization Tier 2",
        examples=["Lan"],
    )
    categorization_tier_3: str = Field(
        serialization_alias="Categorization Tier 3",
        examples=["Disponibilidad"],
    )
    description: str = Field(
        serialization_alias="Description",
        examples=["PR_Indisponibilidad_OBC_LAN_SW_(equipo y estación)"],
    )
    detailed_description: str = Field(
        serialization_alias="Detailed_Decription",
        examples=["PR_Indisponibilidad_OBC_LAN_SW_(equipo y estación)"],
    )
    impact: Literal[
        "1-Extensive/Widespread",
        "2-Significant/Large",
        "3-Moderate/Limited",
        "4-Minor/Localized",
    ] = Field(
        serialization_alias="Impact",
        examples=["4-Minor/Localized"],
    )
    manufacturer: str = Field(
        serialization_alias="Manufacturer",
        examples=["CENIT"],
    )
    product_categorization_tier_1: str = Field(
        serialization_alias="Product Categorization Tier 1",
        examples=["Redes y telecomunicaciones"],
    )
    product_categorization_tier_2: str = Field(
        serialization_alias="Product Categorization Tier 2",
        examples=["Lan"],
    )
    product_categorization_tier_3: str = Field(
        serialization_alias="Product Categorization Tier 3",
        examples=["Switch"],
    )
    service_type: str = Field(
        serialization_alias="Service_Type",
        examples=["User Service Request"],
    )
    urgency: Literal[
        "1-Critical",
        "2-High",
        "3-Medium",
        "4-Low",
    ] = Field(
        serialization_alias="Urgency",
        examples=["4-Low"],
    )

    def to_input(self) -> CreateIncidentInput:
        return CreateIncidentInput(
            assigned_group=self.assigned_group,
            assigned_support_company=self.assigned_support_company,
            assigned_support_organization=self.assigned_support_organization,
            assignee=self.assignee,
            categorization_tier_1=self.categorization_tier_1,
            categorization_tier_2=self.categorization_tier_2,
            categorization_tier_3=self.categorization_tier_3,
            description=self.description,
            detailed_description=self.detailed_description,
            impact=self.impact,
            manufacturer=self.manufacturer,
            product_categorization_tier_1=self.product_categorization_tier_1,
            product_categorization_tier_2=self.product_categorization_tier_2,
            product_categorization_tier_3=self.product_categorization_tier_3,
            service_type=self.service_type,
            urgency=self.urgency,
        )


class CreateIncidentResponse(BaseModel):
    incident_number: str
    request_id: str


class IncidentInfoResponse(BaseModel):
    assigned_group: str
    assignee: str
    categorization_tier_1: str | None
    categorization_tier_2: str | None
    categorization_tier_3: str | None
    description: str
    detailed_description: str
    incident_number: str
    impact: str
    priority: str
    product_categorization_tier_1: str | None
    product_categorization_tier_2: str | None
    product_categorization_tier_3: str | None
    product_name: str | None
    status: str
    submit_date: str
    urgency: str
