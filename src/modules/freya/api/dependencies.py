from typing import Annotated

from fastapi import Depends, Request

from src.modules.freya.application.use_cases import FreyaUseCase
from src.modules.freya.infrastructure.adapters import FreyaAdapter


def get_freya_adapter(request: Request) -> FreyaAdapter:
    return request.app.state.freya


FreyaAdapterDep = Annotated[FreyaAdapter, Depends(get_freya_adapter)]


def get_freya_use_case(adapter: FreyaAdapterDep) -> FreyaUseCase:
    return FreyaUseCase(adapter)


FreyaUseCaseDep = Annotated[FreyaUseCase, Depends(get_freya_use_case)]
