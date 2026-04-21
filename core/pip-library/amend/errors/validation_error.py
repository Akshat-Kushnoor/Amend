# ── ValidationError ──────────────────────────────────────────────────
# Raised when input validation fails (missing fields, constraint violations).

from typing import Any, Optional
from amend.errors.base import AmendError


class ValidationError(AmendError):
    def __init__(
        self,
        message: str,
        context: Optional[str] = None,
        metadata: Optional[dict[str, Any]] = None,
    ):
        super().__init__(message, 'ValidationError', context=context, metadata=metadata)
