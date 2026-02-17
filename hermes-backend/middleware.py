import time
import uuid
import logging
from typing import Callable, Awaitable, Any
from starlette.requests import Request
from starlette.middleware.base import BaseHTTPMiddleware
from hermes_data.logging import set_correlation_id

class CorrelationMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable[[Request], Awaitable[Any]]):
        request_id = request.headers.get("X-Correlation-ID") or str(uuid.uuid4())
        set_correlation_id(request_id)
        
        start_time = time.time()
        
        response = await call_next(request)
        
        process_time = (time.time() - start_time) * 1000
        formatted_process_time = "{0:.2f}".format(process_time)
        
        logging.info({
            "event": "request_processed",
            "method": request.method,
            "path": request.url.path,
            "status_code": response.status_code,
            "process_time_ms": formatted_process_time,
            "correlation_id": request_id,
        })
        
        response.headers["X-Correlation-ID"] = request_id
        return response
