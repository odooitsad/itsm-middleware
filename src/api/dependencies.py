from typing import Annotated

from fastapi import Depends, Request

from src.infrastructure.http.client import HttpxClient
from src.infrastructure.itsm.bmc_helix.adapter import BmcHelixAdapter


def get_bmc_helix_http(request: Request) -> HttpxClient:
    return request.app.state.bmc_helix_http


def get_bmc_helix_adapter(
    http_client: Annotated[HttpxClient, Depends(get_bmc_helix_http)],
) -> BmcHelixAdapter:
    return BmcHelixAdapter(http_client)


BmcHelixHttpDep = Annotated[HttpxClient, Depends(get_bmc_helix_http)]
BmcHelixAdapterDep = Annotated[BmcHelixAdapter, Depends(get_bmc_helix_adapter)]
