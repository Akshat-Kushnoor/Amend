# ── Registry — Append-only NDJSON Log Engine ─────────────────────────
# Stores lean records: key + timestamp + count + context + metadata[].
# Message and location are NOT stored — decoded from key via CoreEngine.
# On-disk format: one JSON line per occurrence; get_all() consolidates.

import json
import os
from pathlib import Path
from typing import Any, Optional

from amend.registry.core_engine import decode as engine_decode


class ErrorRecord:
    """
    A consolidated error record.

    Fields stored on disk:  key, timestamp, context, metadata (one entry per line)
    Fields computed on read: count (occurrences), message, filePath, line, funcName, errorClass
    """

    __slots__ = (
        'key', 'timestamp', 'count',
        'context', 'metadata',
        # decoded fields (populated lazily on first access)
        '_decoded',
    )

    def __init__(
        self,
        key:       str,
        timestamp: str,
        count:     int = 1,
        context:   Optional[str] = None,
        metadata:  Optional[list[dict[str, Any]]] = None,
    ) -> None:
        self.key       = key
        self.timestamp = timestamp
        self.count     = count
        self.context   = context
        self.metadata  = metadata or []
        self._decoded: Optional[dict] = None

    # ── Lazy decode ──────────────────────────────────────────────

    def _ensure_decoded(self) -> None:
        if self._decoded is None:
            try:
                self._decoded = engine_decode(self.key)
            except Exception:
                self._decoded = {}

    @property
    def message(self) -> str:
        self._ensure_decoded()
        return self._decoded.get('message', '')  # type: ignore[union-attr]

    @property
    def file_path(self) -> str:
        self._ensure_decoded()
        return self._decoded.get('filePath', '')  # type: ignore[union-attr]

    @property
    def line(self) -> int:
        self._ensure_decoded()
        return self._decoded.get('line', 0)  # type: ignore[union-attr]

    @property
    def func_name(self) -> str:
        self._ensure_decoded()
        return self._decoded.get('funcName', '')  # type: ignore[union-attr]

    @property
    def error_class(self) -> str:
        self._ensure_decoded()
        return self._decoded.get('errorClass', '')  # type: ignore[union-attr]

    # ── Serialisation ────────────────────────────────────────────

    def to_disk_dict(self) -> dict[str, Any]:
        """Minimal dict for one NDJSON line (one occurrence)."""
        d: dict[str, Any] = {
            'key':       self.key,
            'timestamp': self.timestamp,
        }
        if self.context is not None:
            d['context'] = self.context
        if self.metadata:
            d['metadata'] = self.metadata
        return d

    def to_full_dict(self) -> dict[str, Any]:
        """Full dict including decoded fields — for export / AI agents."""
        self._ensure_decoded()
        return {
            'key':        self.key,
            'errorClass': self.error_class,
            'message':    self.message,
            'filePath':   self.file_path,
            'line':       self.line,
            'funcName':   self.func_name,
            'timestamp':  self.timestamp,
            'count':      self.count,
            'context':    self.context,
            'metadata':   self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> 'ErrorRecord':
        return cls(
            key=data['key'],
            timestamp=data['timestamp'],
            context=data.get('context'),
            metadata=data.get('metadata', []),
        )


class Registry:
    """Singleton append-only NDJSON log registry (lean, metadata-only)."""

    _instance: Optional['Registry'] = None

    def __init__(self) -> None:
        self._dir       = Path.cwd() / '.amend'
        self._file_path = self._dir / 'errors.log'
        self._ensure_dir()

    @classmethod
    def get_instance(cls) -> 'Registry':
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def _ensure_dir(self) -> None:
        self._dir.mkdir(parents=True, exist_ok=True)

    # ── Write ────────────────────────────────────────────────────

    def record(self, error: Any) -> None:
        """
        Append one lean occurrence line to the log.
        metadata must be a list[dict] (one entry per call is typical).
        """
        entry = ErrorRecord(
            key=error.key,
            timestamp=error.timestamp,
            context=getattr(error, 'context', None),
            metadata=getattr(error, 'metadata', []) or [],
        )
        line = json.dumps(entry.to_disk_dict(), separators=(',', ':')) + '\n'
        with open(self._file_path, 'a', encoding='utf-8') as f:
            f.write(line)

    # ── Read ─────────────────────────────────────────────────────

    def get_all(self) -> list[ErrorRecord]:
        """
        Read all raw lines and consolidate by key:
          - count  = number of logged occurrences
          - metadata = all metadata lists merged in order
          - timestamp = most recent occurrence
        """
        if not self._file_path.exists():
            return []
        content = self._file_path.read_text(encoding='utf-8').strip()
        if not content:
            return []

        # consolidate: key → record
        index: dict[str, ErrorRecord] = {}
        for raw_line in content.split('\n'):
            if not raw_line:
                continue
            try:
                data = json.loads(raw_line)
            except json.JSONDecodeError:
                continue

            k = data.get('key', '')
            if not k:
                continue

            if k in index:
                rec = index[k]
                rec.count     += 1
                rec.timestamp  = data['timestamp']  # keep latest
                new_meta = data.get('metadata', [])
                if new_meta:
                    rec.metadata.extend(new_meta)
            else:
                index[k] = ErrorRecord.from_dict(data)

        return list(index.values())

    def find(self, key: str) -> list[ErrorRecord]:
        """Find records whose key equals or starts with the given query."""
        return [r for r in self.get_all() if r.key == key or r.key.startswith(key)]

    def clear(self) -> None:
        """Truncate the log file."""
        if self._file_path.exists():
            self._file_path.write_text('', encoding='utf-8')

    def status(self) -> dict[str, Any]:
        """Return total count + last 5 recent records."""
        all_records = self.get_all()
        return {
            'total':  len(all_records),
            'recent': all_records[-5:],
        }

    def export_to(self, file_path: str, fmt: str) -> None:
        """
        Export registry to a file.
          fmt = "json"  → structured JSON array (with decoded fields)
          fmt = "log"   → human-readable text
        """
        all_records = self.get_all()
        target = Path(file_path)
        target.parent.mkdir(parents=True, exist_ok=True)

        if fmt == 'json':
            content = json.dumps(
                [r.to_full_dict() for r in all_records], indent=2
            )
        else:
            lines = []
            for r in all_records:
                parts = [
                    f'[{r.timestamp}]',
                    r.key,
                    f'{r.error_class}: {r.message}',
                    f'at {r.file_path}:{r.line}',
                ]
                if r.count > 1:
                    parts.append(f'×{r.count}')
                if r.context:
                    parts.append(f'ctx:{r.context}')
                lines.append('  '.join(parts))
            content = '\n'.join(lines) + '\n'

        target.write_text(content, encoding='utf-8')

    @property
    def file_path(self) -> str:
        return str(self._file_path)
