# WHAT DOES THIS FILE DO: Global FastAPI exception handler — turns Shinrai's own exceptions into clean 400s, everything else into a generic 500.

# ================== IMPORTS ==================
from fastapi import Request, status
from fastapi.responses import JSONResponse

from app.core.utils.errors import ShinraiException
# ================== IMPORTS ==================


# =========== FUNCTION ===========
# ROLE: catches anything that escapes a route handler and turns it into a consistent JSON error response
async def exception_handler(request: Request, exc: Exception) -> JSONResponse:
    ''' known Shinrai errors get a 400 with their real message, anything unknown gets a generic 500 '''

    # FLOW-1: a ShinraiException means we already know what went wrong and it's safe to tell the caller
    if isinstance(exc, ShinraiException):
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "error": exc.__class__.__name__,
                "message": str(exc),
                "path": str(request.url),
            },
        )

    # FLOW-2: anything else is unexpected — don't leak internals, just say something broke
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "Internal Server Error",
            "message": "An unexpected error occurred",
            "path": str(request.url),
        },
    )
# =========== FUNCTION ===========
