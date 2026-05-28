from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging
import os

# Set up logging (resilient to container permission restrictions)
log_file = None
if os.environ.get("APP_ENV") != "production":
    try:
        log_file = os.path.join(os.getcwd(), '..', 'backend_errors.log')
        with open(log_file, 'a'):
            pass
    except Exception:
        log_file = None

if log_file:
    logging.basicConfig(
        filename=log_file,
        level=logging.ERROR,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
else:
    logging.basicConfig(
        level=logging.ERROR,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
logger = logging.getLogger("backend_api")

from app.routers import assistant, auth, analytics, tasks

app = FastAPI(
    title="RemindMe Python API",
    version="0.1.0",
    description="Python business-logic API for the Flutter RemindMe client.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", tags=["system"])
def health():
    return {"status": "ok", "service": "remindme-python-api"}


@app.get("/")
async def root():
    return {"status": "online"}


from app.routers import assistant, auth, analytics, tasks, system

app.include_router(auth.router, prefix="/api/v1/auth", tags=["auth"])
app.include_router(tasks.router, prefix="/api/v1/tasks", tags=["tasks"])
app.include_router(assistant.router, prefix="/api/v1/assistant", tags=["assistant"])
app.include_router(analytics.router, prefix="/api/v1/analytics", tags=["analytics"])
app.include_router(system.router, prefix="/api/v1/system", tags=["system"])
