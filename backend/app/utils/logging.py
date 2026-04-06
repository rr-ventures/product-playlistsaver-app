import json
import logging
import sys
from datetime import UTC, datetime

from app.config import get_settings


class StructuredFormatter(logging.Formatter):
    """JSON-line log formatter for machine-parseable log output."""

    def format(self, record: logging.LogRecord) -> str:
        entry: dict = {
            "timestamp": datetime.now(UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        if record.exc_info and record.exc_info[1] is not None:
            entry["exception"] = self.formatException(record.exc_info)
        extra_keys = set(record.__dict__) - set(logging.LogRecord("", 0, "", 0, None, None, None).__dict__)
        for key in sorted(extra_keys):
            if key.startswith("_"):
                continue
            val = getattr(record, key, None)
            if val is not None:
                try:
                    json.dumps(val)
                    entry[key] = val
                except (TypeError, ValueError):
                    entry[key] = str(val)
        return json.dumps(entry)


def configure_logging() -> None:
    settings = get_settings()
    root = logging.getLogger()
    root.setLevel(settings.log_level)

    if root.handlers:
        root.handlers.clear()

    handler = logging.StreamHandler(sys.stdout)
    if settings.environment == "production":
        handler.setFormatter(StructuredFormatter())
    else:
        handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(name)s %(message)s"))
    root.addHandler(handler)
