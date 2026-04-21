# Amend — Python Library Reference

## Overview

The `amend` Python library is the native Python implementation of the cross-language Amend error intelligence system. It is a functional mirror of the NPM package — both share the identical deterministic key format, registry design, and CLI surface. Python exceptions raised through Amend automatically capture their call site, encode location and message into a compact `amend:` key, and append a lean record to the shared local registry at `~/.amend/errors.log`.

When an `AmendError` subclass is raised, the system automatically:
1. Walks the traceback stack to find the caller outside the `amend` package internals.
2. Encodes file path, line number, function name, and the error message into a deterministic `amend:` key via `CoreEngine`.
3. Appends a lean NDJSON record (key + timestamp + optional context/metadata) to `~/.amend/errors.log`.

**Package:** `amend`
**Version:** `0.1.0`
**License:** MIT
**Python requirement:** `>=3.10`
**Build system:** `setuptools >= 68.0`
**Development status:** Alpha

---

## Installation

```bash
pip install amend
```

For local monorepo development, install in editable mode from the library root:

```bash
pip install -e core/pip-library
```

---

## Key Format

All Amend keys follow the format:

```
amend:{CLASS}.{loc_b64u}.{msg_b64u}
```

| Segment     | Description                                                     | Example  |
|-------------|-----------------------------------------------------------------|----------|
| `CLASS`     | 3-character error type code                                     | `SCO`, `NET`, `VAL`, `ERR` |
| `loc_b64u`  | Base64url (no padding) of `"{file_path}|{line}|{func_name}"`   | opaque   |
| `msg_b64u`  | Base64url (no padding) of the error message string              | opaque   |

Decoding is a pure standard-library operation using `base64.urlsafe_b64decode`. No external state is required.

---

## Error Classes

All Amend errors extend `AmendError`, which itself extends the native Python `Exception`. The constructor auto-captures the throw site and registers the error without any manual configuration.

| Class             | Error Code | Intended Use                               |
|-------------------|------------|--------------------------------------------|
| `ScopeError`      | `SCO`      | Guard clause or scope boundary violations  |
| `NetworkError`    | `NET`      | HTTP, socket, or connection failures       |
| `ValidationError` | `VAL`      | Input validation or schema failures        |
| `AmendError`      | `ERR`      | Base class — extend for custom error types |

### Constructor Signature

```python
ScopeError(message: str, context: str | None = None, metadata: dict | list[dict] | None = None)
NetworkError(message: str, context: str | None = None, metadata: dict | list[dict] | None = None)
ValidationError(message: str, context: str | None = None, metadata: dict | list[dict] | None = None)
```

| Parameter  | Type                   | Description                                                    |
|------------|------------------------|----------------------------------------------------------------|
| `message`  | `str`                  | The human-readable error description                           |
| `context`  | `str \| None`          | Optional short tag for grouping (e.g. `"auth"`, `"payments"`) |
| `metadata` | `list[dict] \| None`   | Optional list of dicts for structured payload                  |

### Instance Attributes

Every raised `AmendError` instance exposes:

| Attribute   | Type              | Description                                          |
|-------------|-------------------|------------------------------------------------------|
| `args`      | `tuple`           | The original message (inherited from `Exception`)    |
| `key`       | `str`             | The self-decoding `amend:` key                       |
| `timestamp` | `str`             | ISO-8601 UTC timestamp (e.g. `2026-04-08T10:15:00Z`) |
| `context`   | `str \| None`     | Optional grouping tag                                |
| `metadata`  | `list[dict]`      | Structured payload (empty list if not provided)      |

---

## Usage

### Raising Errors

```python
from amend import ScopeError, NetworkError, ValidationError

# Basic raise
def get_user(user_id: str):
    if not user_id:
        raise ScopeError('User ID must be provided')

# Raise with context and metadata
def fetch_config(url: str):
    if not url:
        raise ValidationError(
            'Configuration URL is required',
            context='bootstrap',
            metadata=[{'step': 'init', 'expected': 'str', 'received': type(url).__name__}],
        )

# Catch and inspect the key
try:
    get_user('')
except ScopeError as e:
    print(e.key)        # amend:SCO.<loc_b64u>.<msg_b64u>
    print(e.timestamp)  # 2026-04-08T10:15:00Z
```

### Decoding a Key

```python
import amend

decoded = amend.engine.decode('amend:VAL.<loc_b64u>.<msg_b64u>')
# Returns a dict:
print(decoded['errorClass'])  # 'ValidationError'
print(decoded['filePath'])    # 'app/services/config.py'
print(decoded['line'])        # 12
print(decoded['funcName'])    # 'fetch_config'
print(decoded['message'])     # 'Configuration URL is required'
```

The dict returned by `decode()` contains:

| Key          | Type    | Description                         |
|--------------|---------|-------------------------------------|
| `key`        | `str`   | The original `amend:` key           |
| `errorClass` | `str`   | Full class name (e.g. `ScopeError`) |
| `filePath`   | `str`   | Relative file path of the throw site|
| `line`       | `int`   | Line number of the throw site        |
| `funcName`   | `str`   | Function name of the throw site      |
| `message`    | `str`   | The error message                   |

---

## API Reference

### `amend.engine` — `CoreEngine`

All methods are module-level functions wrapped in a `CoreEngine` class for ergonomic access. They are pure, stateless, and have no I/O side effects.

| Method / Attribute              | Returns   | Description                                                              |
|---------------------------------|-----------|--------------------------------------------------------------------------|
| `encode(file_path, line, class_name, func_name, message, error_class)` | `str` | Build a self-decoding `amend:` key from raw components |
| `decode(key)`                   | `dict`    | Fully decode a key. Raises `ValueError` on invalid format.               |
| `verify(key)`                   | `bool`    | Return `True` if the key is structurally valid                           |
| `error_class(key)`              | `str`     | Fast extraction of the error class code without a full decode            |
| `location(key)`                 | `dict`    | Fast extraction of `filePath`, `line`, `funcName` only                   |
| `message(key)`                  | `str`     | Fast extraction of the message only                                      |

```python
import amend

# Verify a key before using it
if amend.engine.verify(key):
    loc = amend.engine.location(key)
    print(f"Error at {loc['filePath']}:{loc['line']}")

# Extract just the error class quickly
cls = amend.engine.error_class(key)  # 'ScopeError'
```

### `amend.registry` — `Registry`

The `Registry` singleton manages `~/.amend/errors.log`. All methods are instance methods accessed through the global `amend.registry` singleton.

| Method                          | Returns             | Description                                                     |
|---------------------------------|---------------------|-----------------------------------------------------------------|
| `get_all()`                     | `list[ErrorRecord]` | Read and consolidate all log entries by key. Occurrence counts are tracked via `count`. |
| `find(key)`                     | `list[ErrorRecord]` | Return records whose key equals or starts with the given query. |
| `status()`                      | `dict`              | Returns `{'total': int, 'recent': list[ErrorRecord]}` (last 5). |
| `clear()`                       | `None`              | Truncate the log file.                                          |
| `export_to(file_path, fmt)`     | `None`              | Write all records to a file. `fmt` is `'json'` or `'log'`.     |
| `file_path` (property)          | `str`               | Absolute path to the active log file.                           |

The `ErrorRecord` class exposes the following properties (decoded lazily from the key on first access):

| Property      | Type    | Description                              |
|---------------|---------|------------------------------------------|
| `key`         | `str`   | The `amend:` key                         |
| `timestamp`   | `str`   | ISO-8601 UTC timestamp (most recent)     |
| `count`       | `int`   | Total number of occurrences logged       |
| `context`     | `str \| None` | Optional grouping tag              |
| `metadata`    | `list[dict]`  | Merged metadata from all occurrences|
| `message`     | `str`   | Decoded error message (lazy)             |
| `file_path`   | `str`   | Decoded throw-site file path (lazy)      |
| `line`        | `int`   | Decoded throw-site line number (lazy)    |
| `func_name`   | `str`   | Decoded throw-site function name (lazy)  |
| `error_class` | `str`   | Decoded error class name (lazy)          |

```python
import amend

records = amend.registry.get_all()
for r in records:
    print(f"{r.error_class} at {r.file_path}:{r.line} — seen {r.count}x")

status = amend.registry.status()
print(f"Total: {status['total']}, Recent: {len(status['recent'])}")
```

### `amend.ai` — `AgentConfig`

The `AgentConfig` singleton controls which file paths are visible to AI agents and manages per-key diagnostic hints.

| Method / Property               | Description                                                           |
|---------------------------------|-----------------------------------------------------------------------|
| `enable(scope)`                 | Enable AI handling for errors originating from the given path prefix  |
| `disable(scope)`                | Disable AI handling for errors from the given path prefix             |
| `is_enabled(file_path)`         | Return `True` if the given path falls within an enabled scope         |
| `enabled_scopes` (property)     | List of currently enabled scope prefixes                              |
| `disabled_scopes` (property)    | List of currently disabled scope prefixes                             |
| `set_hint(hash, hint)`          | Attach a hint string to a specific `amend:` key                       |
| `set(hash, hint)`               | Alias for `set_hint`                                                  |
| `get_hint(hash)`                | Retrieve the hint for a key. Returns `None` if not set.               |
| `clear_hint(hash)`              | Remove the hint for a key                                             |
| `all_hints` (property)          | Dict of all registered `{key: hint}` pairs                            |

Scope resolution rules: disabled scopes are evaluated first; if a file path matches any disabled scope, it is excluded regardless of enabled scopes. If no enabled scope is configured, all paths are enabled by default.

```python
import amend

# Enable agent handling only for the payments module
amend.ai.enable('app/payments')

# Suppress noisy test-fixture errors
amend.ai.disable('tests/fixtures')

# Attach a human-authored hint to a recurring error
amend.ai.set_hint(
    'amend:NET.<loc_b64u>.<msg_b64u>',
    'This timeout is caused by upstream rate-limiting. Increase retry backoff to 2s.'
)

# Check whether a path is in scope
active = amend.ai.is_enabled('app/payments/gateway.py')  # True
```

---

## CLI Reference

The `amend` binary is registered automatically via the `project.scripts` entry in `pyproject.toml`. All commands operate on `~/.amend/errors.log`.

### `amend drawErrors`

List all registered errors in a tabular format.

```
amend drawErrors

KEY                                                     MESSAGE
amend:SCO.<loc>.<msg>                                   User ID must be provided
amend:VAL.<loc>.<msg>                                   Configuration URL is required
```

### `amend pin <hash>`

Show the full decoded details for a single error by its `amend:` key. Falls back to direct key decoding if the key is not present in the local registry.

```
amend pin "amend:SCO.<loc_b64u>.<msg_b64u>"

[amend pin amend:SCO.<loc_b64u>.<msg_b64u>]

  Message    : User ID must be provided
  ErrorClass : ScopeError
  File       : app/services/user.py:22
  Function   : get_user
  Timestamp  : 2026-04-08T10:15:00Z
  Count      : 3
  Context    : (none)
  Metadata   : (none)
```

### `amend registry [status]`

Show registry summary including total count, recent errors, most common error type, and errors in the last 24 hours.

```
amend registry status

[amend registry status]

  Total errors    : 12
  Recent errors   : 5

  KEY                            MESSAGE                   FILE
  amend:...                      User ID must be provided  app/services/user.py:22

  Analytics:
    Most common type  : ValidationError (7x)
    Last 24h          : 4 errors
```

### `amend clean [registry]`

Interactively confirm and clear all entries from the registry.

```
amend clean registry
Are you sure you want to clear the entire registry? [y/N] y
Registry cleared.
```

### `amend logRegistry <filepath>`

Export all registry records to a file. The file extension determines the format:
- `.json` — structured JSON array with all decoded fields (`to_full_dict()`)
- `.log` — human-readable plain-text format

```bash
amend logRegistry ./reports/errors.json
amend logRegistry ./reports/errors.log
```

---

## Registry Storage

The registry file is stored at:

- **Location:** `~/.amend/errors.log` (created automatically on first raise)
- **Format:** Newline-delimited JSON (NDJSON) — one JSON object per line, one line per occurrence
- **Disk record fields:** `key`, `timestamp`, `context` (optional), `metadata` (optional)
- **Message and location are NOT stored on disk** — they are recovered lazily on read by decoding the key via `CoreEngine`

This keeps the log compact and avoids storing redundant string data for recurring errors.

---

## Test Suite

The library includes three test modules in `tests/`:

| File                        | Coverage                                                          |
|-----------------------------|-------------------------------------------------------------------|
| `test_hash_basic.py`        | Fundamental encode/decode/verify round-trip tests                 |
| `test_hash_components.py`   | Segment-level validation of CLASS, loc_b64u, and msg_b64u fields  |
| `test_hash_determinism.py`  | Confirms that identical inputs always produce identical keys       |

Run the tests with:

```bash
pytest
```

---

## Cross-Language Compatibility

The Python and Node.js implementations are wire-compatible. A key generated by the Python library can be decoded by the JavaScript `CoreEngine` and vice versa. Both:
- Use the same `amend:{CLASS}.{loc_b64u}.{msg_b64u}` format.
- Apply the same 3-character error code mapping (`SCO`, `NET`, `VAL`, `ERR`).
- Use URL-safe Base64 with no padding for both segments.
- Write to the same `~/.amend/errors.log` registry file.
