# ── AmendError — Base Exception Class ────────────────────────────────
# Auto-extracts throw location from traceback, builds a self-decoding
# CoreEngine key, and records lean metadata to the NDJSON registry.

import os
import traceback
from datetime import datetime, timezone
from typing import Any, Optional

from amend.registry.core_engine import encode as engine_encode
from amend.registry.registry import Registry


class AmendError(Exception):
    """
    Base error class for the Amend system.

    Attributes:
        key       — self-decoding amend: key (encodes location + message)
        timestamp — ISO-8601 UTC string
        context   — optional string tag
        metadata  — list of dicts (user-supplied key/value pairs)
    """

    def __init__(
        self,
        message:     str,
        error_class: str,
        context:     Optional[str]             = None,
        metadata:    Optional[list[dict[str, Any]]] = None,
    ) -> None:
        super().__init__(message)
        self.timestamp: str = (
            datetime.now(timezone.utc)
            .replace(microsecond=0)
            .isoformat()
            .replace('+00:00', 'Z')
        )

        # ── Auto-extract throw site from traceback ───────────────
        file_path = 'unknown'
        line      = 0
        class_name = ''
        func_name  = 'unknown'

        stack = traceback.extract_stack()
        for frame in reversed(stack):
            normalized = frame.filename.replace('\\', '/')
            if '/amend/' in normalized and (
                'errors/' in normalized or 'registry/' in normalized
            ):
                continue
            file_path  = os.path.relpath(frame.filename).replace('\\', '/')
            line       = frame.lineno
            func_name  = frame.name
            break

        # ── Build self-decoding key via CoreEngine ───────────────
        self.key: str = engine_encode(
            file_path, line, class_name, func_name, message, error_class
        )

        # ── Bind optional fields ─────────────────────────────────
        self.context:  Optional[str]              = context
        self.metadata: list[dict[str, Any]]       = metadata or []

        # ── Auto-register lean record to NDJSON log ──────────────
        Registry.get_instance().record(self)
