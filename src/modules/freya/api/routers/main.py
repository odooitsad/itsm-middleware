from fastapi import APIRouter

from src.modules.freya.api.routers import incidents, zabbix

freya_router = APIRouter(prefix="/freya", tags=["Freya"])
freya_router.include_router(incidents.router, prefix="/clients/incidents")
freya_router.include_router(zabbix.router, prefix="/zabbix/incidents")
