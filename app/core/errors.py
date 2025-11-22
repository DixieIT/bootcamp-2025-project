from fastapi import Request
from fastapi.responses import JSONResponse
import logging
import traceback

logger = logging.getLogger(__name__)

def http_error_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {exc}")
    logger.error(traceback.format_exc())
    return JSONResponse(status_code=500, content={"detail": str(exc)})