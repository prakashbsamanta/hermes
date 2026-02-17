import logging
import json
import sys
from contextvars import ContextVar
from datetime import datetime
from typing import Optional, Dict, Any

# Context variable for request tracing
_correlation_id: ContextVar[Optional[str]] = ContextVar("correlation_id", default=None)

def get_correlation_id() -> Optional[str]:
    """Get current correlation ID."""
    return _correlation_id.get()

def set_correlation_id(correlation_id: str) -> None:
    """Set current correlation ID."""
    _correlation_id.set(correlation_id)

class JSONFormatter(logging.Formatter):
    """JSON log formatter with correlation ID support."""
    
    def format(self, record: logging.LogRecord) -> str:
        log_obj: Dict[str, Any] = {
            "timestamp": datetime.fromtimestamp(record.created).isoformat(),
            "level": record.levelname,
            "message": record.getMessage(),
            "logger": record.name,
            "module": record.module,
            "line": record.lineno,
        }
        
        # Add correlation ID
        correlation_id = get_correlation_id()
        if correlation_id:
            log_obj["correlation_id"] = correlation_id
            
        # Add exception info
        if record.exc_info:
            log_obj["exc_info"] = self.formatException(record.exc_info)
            
        return json.dumps(log_obj)

class ContextFilter(logging.Filter):
    """Filter to inject correlation ID into log records."""
    def filter(self, record):
        record.correlation_id = get_correlation_id() or "N/A"
        return True

def configure_logging(level: str = "INFO", json_format: bool = True) -> None:
    """Configure structured logging."""
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    
    handler = logging.StreamHandler(sys.stdout)
    
    if json_format:
        formatter: logging.Formatter = JSONFormatter()
    else:
        # Inject context filter for text logs
        handler.addFilter(ContextFilter())
        formatter = logging.Formatter(
            "%(asctime)s [%(levelname)s] [%(name)s] [Trace: %(correlation_id)s] %(message)s"
        )
        # For simplicity, JSON is preferred here.
    
    handler.setFormatter(formatter)
    
    # Remove existing handlers
    for h in root_logger.handlers[:]:
        root_logger.removeHandler(h)
        
    root_logger.addHandler(handler)
    
    # Log SQL if DEBUG level
    if level == "DEBUG":
        logging.getLogger("sqlalchemy.engine").setLevel(logging.INFO)
