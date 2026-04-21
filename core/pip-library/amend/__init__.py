# ── Amend — Python Public API ────────────────────────────────────────
# import amend
# raise amend.ScopeError("user not found")
# amend.engine.decode(error.key)

from amend.errors.scope_error import ScopeError
from amend.errors.network_error import NetworkError
from amend.errors.validation_error import ValidationError
from amend.registry.registry import Registry
from amend.registry.core_engine import CoreEngine
from amend.ai.agent_config import AgentConfig

# ── Singleton instances ──────────────────────────────────────────────
registry = Registry.get_instance()
engine   = CoreEngine()
ai       = AgentConfig.get_instance()

__all__ = [
    'ScopeError',
    'NetworkError',
    'ValidationError',
    'registry',
    'engine',
    'ai',
    'CoreEngine',
]
