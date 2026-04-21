# ── NetworkError ─────────────────────────────────────────────────────
# Raised when an outbound network call fails.

from typing import Any, Optional
from amend.errors.base import AmendError


class NetworkError(AmendError):
    def __init__(
        self,
        message: str,
        context: Optional[str] = None,
        metadata: Optional[dict[str, Any]] = None,
    ):
        super().__init__(message, 'NetworkError', context=context, metadata=metadata)
