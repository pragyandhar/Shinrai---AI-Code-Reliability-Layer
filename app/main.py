# WHAT DOES THIS FILE DO: FastAPI app entry point — initializes the app and registers all routes.

# ================== IMPORTS ==================
from fastapi import FastAPI
# ================== IMPORTS ==================


# =========== VARIABLES : FastAPI app instance ===========
app = FastAPI(
    title="Shinrai",
    version="1.0.0",
    description="AI Code Reliability Layer — validates, scores and audits LLM-generated code."
)
# =========== VARIABLES : FastAPI app instance ===========


# =========== FUNCTION ===========
# ROLE: health check so we know the service is up
@app.get("/health")
def health_check() -> dict:
    ''' Returns service status — simple alive check '''

    return {"status": "ok", "service": "Shinrai"}
# =========== FUNCTION ===========