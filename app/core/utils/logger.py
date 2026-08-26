# WHAT DOES THIS FILE DO: Structured JSON logging for pipeline execution — one line per event, easy to grep or ship to a log collector.

# ================== IMPORTS ==================
import json
import logging
from datetime import datetime
from typing import Any
# ================== IMPORTS ==================


# =========== FUNCTION ===========
# ROLE: wraps Python's logging module so every pipeline event comes out as one JSON line with a consistent shape
class StructuredLogger:
    ''' every log line carries a timestamp, an event name and a task_id, plus whatever extra data the caller passes '''

    def __init__(self, name: str):
        self.logger = logging.getLogger(name)
        self._setup_handlers()

    # FLOW-1: console handler with a plain formatter — the structure lives inside the message itself, as JSON
    def _setup_handlers(self) -> None:
        ''' attaches one stream handler, only once, so repeated instantiation doesn't duplicate log lines '''

        if self.logger.handlers:
            return

        handler = logging.StreamHandler()
        formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)
        self.logger.setLevel(logging.INFO)

    # FLOW-2: normal pipeline events — step started, step finished, score calculated, etc
    def log_event(self, event: str, task_id: str, data: dict[str, Any]) -> None:
        ''' bundles event name + task_id + timestamp + whatever data the caller wants recorded, logs it as JSON '''

        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "event": event,
            "task_id": task_id,
            **data,
        }

        self.logger.info(json.dumps(log_entry))

    # FLOW-3: failures — same shape as log_event but at error level, with room for a traceback
    def log_error(self, event: str, task_id: str, error: str, trace: str = "") -> None:
        ''' same idea as log_event but always includes the error message and, optionally, a traceback string '''

        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "event": event,
            "task_id": task_id,
            "error": error,
            "traceback": trace,
        }

        self.logger.error(json.dumps(log_entry))
# =========== FUNCTION ===========


# =========== VARIABLES : one shared logger instance for the whole pipeline, import this everywhere instead of making new ones ===========
pipeline_logger = StructuredLogger("shinrai.pipeline")
# =========== VARIABLES : one shared logger instance for the whole pipeline, import this everywhere instead of making new ones ===========
