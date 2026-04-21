# ── AgentConfig — amend.ai namespace ─────────────────────────────────
# Provides scoped AI enable/disable controls and per-hash hints.

from typing import Optional


class AgentConfig:
    """Singleton managing AI agent scope control and per-hash hints."""

    _instance: Optional['AgentConfig'] = None

    def __init__(self) -> None:
        self._enabled_scopes: set[str] = set()
        self._disabled_scopes: set[str] = set()
        self._hints: dict[str, str] = {}

    @classmethod
    def get_instance(cls) -> 'AgentConfig':
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    # ── Scope control ────────────────────────────────────────────

    def enable(self, scope: str) -> None:
        """Enable AI agent handling for errors from the given scope path."""
        self._enabled_scopes.add(scope)
        self._disabled_scopes.discard(scope)

    def disable(self, scope: str) -> None:
        """Disable AI agent handling for errors from the given scope path."""
        self._disabled_scopes.add(scope)
        self._enabled_scopes.discard(scope)

    def is_enabled(self, file_path: str) -> bool:
        """Check if a given file path falls within an AI-enabled scope."""
        for scope in self._disabled_scopes:
            if file_path.startswith(scope):
                return False
        if not self._enabled_scopes:
            return True
        return any(file_path.startswith(scope) for scope in self._enabled_scopes)

    @property
    def enabled_scopes(self) -> list[str]:
        return list(self._enabled_scopes)

    @property
    def disabled_scopes(self) -> list[str]:
        return list(self._disabled_scopes)

    # ── Hint management ──────────────────────────────────────────

    def set_hint(self, hash: str, hint: str) -> None:
        """Attach a human-authored hint to a specific error hash."""
        self._hints[hash] = hint

    # Convenience alias used by amend.ai.hints.set(...)
    set = set_hint

    def get_hint(self, hash: str) -> Optional[str]:
        """Retrieve the hint for a specific error hash."""
        return self._hints.get(hash)

    def clear_hint(self, hash: str) -> None:
        """Remove a hint for a specific error hash."""
        self._hints.pop(hash, None)

    @property
    def all_hints(self) -> dict[str, str]:
        return dict(self._hints)
