from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fastapi import Request, HTTPException
import os

# Get Redis URL from env or default to memory
redis_url = os.getenv("REDIS_URL", "memory://")

# Create limiter instance
# For production using Redis: storage_uri="redis://localhost:6379"
limiter = Limiter(
    key_func=get_remote_address,
    storage_uri=redis_url,
    default_limits=["200/hour"]
)

def custom_rate_limit_handler(request: Request, exc: RateLimitExceeded):
    """
    Custom handler for rate limit exceeded exceptions.
    Returns a JSON response with 429 status code and retry info.
    """
    # Extract retry after time from exception detail if available
    detail = str(exc)
    retry_after = "60 seconds"
    
    # Try to parse "Retry after X seconds" from detail
    if "Retry after" in detail:
        parts = detail.split("Retry after")
        if len(parts) > 1:
            retry_after = parts[1].strip()

    raise HTTPException(
        status_code=429,
        detail={
            "message": "Too many requests. Please try again later.",
            "retry_after": retry_after
        }
    )
