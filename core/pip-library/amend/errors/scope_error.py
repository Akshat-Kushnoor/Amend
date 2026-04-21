# ── ScopeError ───────────────────────────────────────────────────────
# Raised when a guard clause or scope boundary condition fails.

from typing import Any, Optional
from amend.errors.base import AmendError


class ScopeError(AmendError):
    def __init__(
        self,
        message: str,
        context: Optional[str] = None,
        metadata: Optional[dict[str, Any]] = None,
    ):
        super().__init__(message, 'ScopeError', context=context, metadata=metadata)
