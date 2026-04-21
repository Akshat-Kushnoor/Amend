# ── __init__.py for errors subpackage ─────────────────────────────────
from amend.errors.base import AmendError
from amend.errors.scope_error import ScopeError
from amend.errors.network_error import NetworkError
from amend.errors.validation_error import ValidationError

__all__ = ['AmendError', 'ScopeError', 'NetworkError', 'ValidationError']
