from fastapi import APIRouter

from src.modules.bmc_helix.api.routers import incidents, zabbix

bmc_helix_router = APIRouter()
bmc_helix_router.include_router(incidents.router)
bmc_helix_router.include_router(zabbix.router)
