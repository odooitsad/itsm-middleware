from fastapi import Depends, HTTPException, status
from fastapi.security import APIKeyHeader, HTTPBearer

from src.core.config import get_settings

settings = get_settings()
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=True)

bearer_scheme = HTTPBearer()


async def verify_api_key(api_key: str = Depends(api_key_header)):
    if api_key != settings.API_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API Key",
        )
    return api_key
