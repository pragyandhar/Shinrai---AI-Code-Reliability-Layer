# WHAT DOES THIS FILE DO: FastAPI app entry point — initializes the app, DB and registers all routes.

# ================== IMPORTS ==================
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.models.db import init_db
from app.api.routes import generate, report
# ================== IMPORTS ==================


# =========== FUNCTION ===========
# ROLE: manages app startup and shutdown — DB init happens before the app starts taking requests
@asynccontextmanager
async def lifespan(app: FastAPI):
    ''' initializes DB on startup, yield hands control to the app, shutdown logic goes after yield '''

    init_db()
    yield

# =========== FUNCTION ===========


# =========== VARIABLES : FastAPI app instance ===========
app = FastAPI(
    title="Shinrai",
    version="1.0.0",
    description="AI Code Reliability Layer — validates, scores and audits LLM-generated code.",
    lifespan=lifespan,
)
# =========== VARIABLES : FastAPI app instance ===========


# =========== FUNCTION ===========
# ROLE: health check so we know the service is up
@app.get("/health")
def health_check() -> dict:
    ''' Returns service status — simple alive check '''

    return {"status": "ok", "service": "Shinrai"}

# =========== FUNCTION ===========


# =========== VARIABLES : route registration ===========
app.include_router(generate.router, prefix="/api/v1")
app.include_router(report.router, prefix="/api/v1")
# =========== VARIABLES : route registration ===========
