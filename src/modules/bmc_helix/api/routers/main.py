from fastapi import APIRouter

from src.modules.bmc_helix.api.routers import incidents, zabbix

bmc_helix_router = APIRouter(prefix="/bmc-helix")
bmc_helix_router.include_router(
    incidents.router, prefix="/clients/incidents", tags=["BMC-Helix / Clients"]
)
bmc_helix_router.include_router(
    zabbix.router, prefix="/zabbix/incidents", tags=["BMC-Helix / Zabbix"]
)
