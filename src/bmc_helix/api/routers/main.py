from fastapi import APIRouter

from src.bmc_helix.api.routers import incidents

bmc_helix_router = APIRouter()
bmc_helix_router.include_router(incidents.router)
