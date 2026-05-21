from pydantic import BaseModel, Field


class CreateIncidentRequest(BaseModel):
    first_name: str = Field("Integracion", serialization_alias="First_Name")
    last_name: str = Field("Datasmart", serialization_alias="Last_Name")
    company: str = Field("CENIT", serialization_alias="Company")
    direct_contact_first_name: str = Field(
        "Integracion", serialization_alias="Direct Contact First Name"
    )
    direct_contact_last_name: str = Field(
        "Datasmart", serialization_alias="Direct Contact Last Name"
    )
    description: str = Field(
        "PR_Indisponibilidad_OBC_LAN_SW_(equipo y estación)",
        serialization_alias="Description",
    )
    detailed_description: str = Field(
        "PR_Indisponibilidad_OBC_LAN_SW_(equipo y estación)",
        serialization_alias="Detailed_Decription",
    )
    status: str = Field("Assigned", serialization_alias="Status")
    impact: str = Field("4-Minor/Localized", serialization_alias="Impact")
    urgency: str = Field("4-Low", serialization_alias="Urgency")
    service_type: str = Field(
        "User Service Request", serialization_alias="Service_Type"
    )
    reported_source: str = Field("Self Service", serialization_alias="Reported Source")
    categorization_tier_1: str = Field(
        "Redes y telecomunicaciones", serialization_alias="Categorization Tier 1"
    )
    categorization_tier_2: str = Field(
        "Lan", serialization_alias="Categorization Tier 2"
    )
    categorization_tier_3: str = Field(
        "Disponibilidad", serialization_alias="Categorization Tier 3"
    )
    product_categorization_tier_1: str = Field(
        "Redes y telecomunicaciones",
        serialization_alias="Product Categorization Tier 1",
    )
    product_categorization_tier_2: str = Field(
        "Lan", serialization_alias="Product Categorization Tier 2"
    )
    product_categorization_tier_3: str = Field(
        "Switch", serialization_alias="Product Categorization Tier 3"
    )
    manufacturer: str = Field("CENIT", serialization_alias="Manufacturer")
    assigned_support_company: str = Field(
        "CENIT", serialization_alias="Assigned Support Company"
    )
    assigned_support_organization: str = Field(
        "Soporte Tecnico", serialization_alias="Assigned Support Organization"
    )
    assigned_group: str = Field("Sop_Telco", serialization_alias="Assigned Group")
    assignee: str = Field(
        "Jesus Alberto de La Hoz Jimenez", serialization_alias="Assignee"
    )
    action: str = Field("CREATE", serialization_alias="z1D_Action")


class CreateIncidentResponse(BaseModel):
    incident_number: str
    request_id: str
