from fastapi import APIRouter, Request
import logging
import os
from pydantic import BaseModel

router = APIRouter()
logger = logging.getLogger("system_api")

class LogRequest(BaseModel):
    message: str
    level: str = "ERROR"

@router.post("/log")
async def log_error(payload: LogRequest):
    if payload.level == "ERROR":
        logger.error(f"CLIENT ERROR: {payload.message}")
    elif payload.level == "WARNING":
        logger.warning(f"CLIENT WARNING: {payload.message}")
    else:
        logger.info(f"CLIENT INFO: {payload.message}")
    return {"status": "logged"}
@router.get("/logs")
async def get_logs():
    try:
        log_file = os.path.join(os.getcwd(), '..', 'backend_errors.log')
        if not os.path.exists(log_file):
            return {"logs": "No logs found."}
        with open(log_file, "r") as f:
            lines = f.readlines()
            return {"logs": "".join(lines[-50:])} # Last 50 lines
    except Exception as e:
        return {"logs": f"Error reading logs: {e}"}
