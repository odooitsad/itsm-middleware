from fastapi import APIRouter

from src.modules.its_helpdesk.api.routers import tickets, zabbix

its_helpdesk_router = APIRouter(prefix="/its-helpdesk")
its_helpdesk_router.include_router(
    tickets.router, prefix="/tickets", tags=["ITS Helpdesk / Clients"]
)
its_helpdesk_router.include_router(
    zabbix.router, prefix="/zabbix", tags=["ITS Helpdesk / Zabbix"]
)
