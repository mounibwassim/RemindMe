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

@router.get("/smtp-test")
async def test_smtp_configuration():
    from backend.config import SMTP_HOST, SMTP_PORT, SMTP_USERNAME, SMTP_PASSWORD
    import smtplib
    
    diagnostics = {
        "smtp_host": SMTP_HOST,
        "smtp_port": SMTP_PORT,
        "smtp_username_configured": bool(SMTP_USERNAME),
        "smtp_username": SMTP_USERNAME,
        "smtp_password_configured": bool(SMTP_PASSWORD),
        "connection_success": False,
        "tls_success": False,
        "auth_success": False,
        "error": None
    }
    
    try:
        # 1. Connect
        logger.info(f"SMTP Diagnostics: Connecting to {SMTP_HOST}:{SMTP_PORT}")
        server = smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=10)
        diagnostics["connection_success"] = True
        
        # 2. STARTTLS
        logger.info("SMTP Diagnostics: Starting TLS")
        status, response = server.starttls()
        diagnostics["tls_status_code"] = status
        diagnostics["tls_response"] = response.decode('utf-8', errors='ignore') if isinstance(response, bytes) else str(response)
        if status == 220:
            diagnostics["tls_success"] = True
        else:
            diagnostics["error"] = f"STARTTLS failed with status {status}: {diagnostics['tls_response']}"
            server.quit()
            return diagnostics
            
        # 3. Login
        if SMTP_USERNAME and SMTP_PASSWORD:
            logger.info(f"SMTP Diagnostics: Logging in as {SMTP_USERNAME}")
            server.login(SMTP_USERNAME, SMTP_PASSWORD)
            diagnostics["auth_success"] = True
        else:
            diagnostics["error"] = "SMTP credentials missing"
            
        server.quit()
    except Exception as e:
        import traceback
        logger.error(f"SMTP Diagnostics Error: {e}\n{traceback.format_exc()}")
        diagnostics["error"] = str(e)
        
    return diagnostics

