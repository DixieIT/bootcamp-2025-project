from fastapi import Request
from fastapi.responses import JSONResponse

def http_error_handler(request: Request, exc: Exception):
    return JSONResponse(status_code=500, content={"detail": str(exc)})