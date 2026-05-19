import time
from fastapi import Request, HTTPException

# Simple in-memory token bucket / request counter for rate limiting
# Format: { "ip_or_email": [(timestamp), (timestamp)] }
_RATE_LIMITS = {}

def check_rate_limit(key: str, max_requests: int = 5, window_minutes: int = 15):
    """
    Raises HTTPException 429 if the rate limit is exceeded.
    """
    now = time.time()
    window_seconds = window_minutes * 60
    
    if key not in _RATE_LIMITS:
        _RATE_LIMITS[key] = []
        
    # Clean old requests
    _RATE_LIMITS[key] = [ts for ts in _RATE_LIMITS[key] if now - ts < window_seconds]
    
    if len(_RATE_LIMITS[key]) >= max_requests:
        raise HTTPException(
            status_code=429, 
            detail=f"Too many requests. Please try again in {window_minutes} minutes."
        )
        
    _RATE_LIMITS[key].append(now)
