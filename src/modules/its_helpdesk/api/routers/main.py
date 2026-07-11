from fastapi import APIRouter

from src.modules.its_helpdesk.api.routers import tickets, zabbix

its_helpdesk_router = APIRouter(prefix="/its-helpdesk", tags=["ITS Helpdesk"])
its_helpdesk_router.include_router(tickets.router, prefix="/clients/tickets")
its_helpdesk_router.include_router(zabbix.router, prefix="/zabbix/tickets")
