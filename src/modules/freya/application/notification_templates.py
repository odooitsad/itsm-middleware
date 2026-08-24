from src.core.logger import get_logger
from src.core.utils.date_utils import parse_date_format

logger = get_logger(__name__)


def build_im_created_success_template(**kwargs) -> dict[str, str]:
    start_event = parse_date_format(kwargs.get("start_date", ""))
    service_type = kwargs.get("service_type")
    hostname = kwargs.get("hostname")
    description = f"{service_type} {hostname}"

    template = {
        "tipo_plantilla": "apertura",
        "ticket": kwargs.get("im_id"),
        "tipo_servicio": service_type,
        "estado_servicio": kwargs.get("state_service"),
        "servicio": kwargs.get("affected_ci"),
        "estado_enlace": kwargs.get("state_link"),
        "proveedor": kwargs.get("provider"),
        "hora_inicio": start_event,
        "hora_fin": "",
        "descripcion": description,
        "ciudad": kwargs.get("city"),
        "causa": "En diagnóstico",
        "acciones": (
            "Se procede con la revisión y escalamiento para descartes de primer nivel."
        ),
    }
    return template


def build_im_creation_failure_template(**kwargs) -> dict[str, str]:
    start_event = parse_date_format(kwargs.get("start_date", ""))
    hostname = kwargs.get("hostname", "")
    service = kwargs.get("affected_ci", "Desconocido")

    template = {
        "tipo_plantilla": "novedad",
        "tipo_caida": kwargs.get("state_service"),
        "sede": hostname,
        "servicio": service,
        "fecha_hora": start_event,
    }
    return template


def build_im_closed_template(**kwargs) -> dict[str, str]:
    start_event = parse_date_format(kwargs.get("start_date", ""))
    close_event = parse_date_format(kwargs.get("service_end_date", ""))

    template = {
        "tipo_plantilla": "cierre",
        "ticket": kwargs.get("im_id"),
        "tipo_servicio": kwargs.get("service_type"),
        "estado_servicio": "Recuperado",
        "servicio": kwargs.get("affected_ci", "Desconocido"),
        "estado_enlace": "Operativo",
        "proveedor": kwargs.get("provider"),
        "hora_inicio": start_event,
        "hora_fin": close_event,
        "descripcion": kwargs.get("hostname", ""),
        "ciudad": kwargs.get("city"),
    }
    return template
