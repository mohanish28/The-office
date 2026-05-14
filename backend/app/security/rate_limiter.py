from slowapi import Limiter
from starlette.requests import Request

from app.config import settings


def _get_client_ip(request: Request) -> str:
    if settings.BEHIND_PROXY:
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[-1].strip()
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip.strip()
    return request.client.host if request.client else "127.0.0.1"


limiter = Limiter(key_func=_get_client_ip, default_limits=["60/minute"])
