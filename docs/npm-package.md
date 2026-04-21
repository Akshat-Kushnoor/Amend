# Amend — NPM Package Reference

## Overview

The `amend` NPM package is a cross-language error intelligence system for Node.js and TypeScript projects. Its core design principle is the **self-decoding key**: every error thrown through the Amend system encodes its full location and message directly into a compact, Base64url-encoded string prefixed with `amend:`. This means no external database or lookup table is needed to recover error details — the key is entirely self-contained.

When an `AmendError` is thrown, the system automatically:
1. Extracts the throw site from the call stack (file path, line number, function name).
2. Encodes that information along with the error message into a deterministic `amend:` key via `CoreEngine`.
3. Appends a lean record (key + timestamp + optional context/metadata) to the local NDJSON registry at `~/.amend/errors.log`.

**Package:** `amend`
**Version:** `0.1.0`
**License:** MIT
**Node requirement:** `>=18.0.0`
**Build outputs:** Dual CJS (`dist/cjs/`) and ESM (`dist/esm/`) bundles.

---

## Installation

```bash
npm install amend
```

For local monorepo development, link to the built package directly:

```bash
# From inside core/npm-package, build first
npm run build

# In your consuming project's package.json
# "amend": "file:../../core/npm-package"
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
| `loc_b64u`  | Base64url of `"{filePath}|{line}|{funcName}"`                   | opaque   |
| `msg_b64u`  | Base64url of the error message string                           | opaque   |

The three segments are separated by dots. Decoding is a pure standard-library operation — split on dot, Base64url-decode each segment, split the location on pipe.

---

## Error Classes

All Amend errors extend `AmendError`, which itself extends the native `Error`. The constructor automatically captures the throw location and registers the error.

| Class             | Error Code | Intended Use                               |
|-------------------|------------|--------------------------------------------|
| `ScopeError`      | `SCO`      | Guard clause or scope boundary violations  |
| `NetworkError`    | `NET`      | HTTP, socket, or connection failures       |
| `ValidationError` | `VAL`      | Input validation or schema failures        |
| `AmendError`      | `ERR`      | Base class — use directly for custom types |

### Constructor Signature

```typescript
new ScopeError(message: string, options?: AmendErrorOptions)
new NetworkError(message: string, options?: AmendErrorOptions)
new ValidationError(message: string, options?: AmendErrorOptions)
```

```typescript
interface AmendErrorOptions {
  context?:  string;                       // Short string tag for grouping (e.g. "auth", "payments")
  metadata?: Record<string, unknown>[];    // Array of key/value dicts for structured payload
}
```

### Instance Properties

Every thrown `AmendError` instance exposes the following properties:

| Property    | Type                           | Description                                          |
|-------------|--------------------------------|------------------------------------------------------|
| `message`   | `string`                       | The original error message (inherited from `Error`)  |
| `name`      | `string`                       | The error class name (e.g. `"ScopeError"`)          |
| `key`       | `string`                       | The self-decoding `amend:` key                       |
| `timestamp` | `string`                       | ISO-8601 UTC timestamp of creation                   |
| `context`   | `string \| undefined`          | Optional grouping tag passed in options              |
| `metadata`  | `Record<string, unknown>[]`    | Optional structured payload passed in options        |
| `stack`     | `string \| undefined`          | Native stack trace (inherited from `Error`)          |

---

## Usage

### Throwing Errors

```typescript
import { ScopeError, NetworkError, ValidationError } from 'amend';

// Basic throw
function getUser(userId: string) {
  if (!userId) {
    throw new ScopeError('User ID must be provided');
  }
}

// Throw with context and metadata
async function fetchConfig(url: string) {
  if (!url) {
    throw new ValidationError('Configuration URL is required', {
      context: 'bootstrap',
      metadata: [{ step: 'init', expected: 'string', received: typeof url }],
    });
  }
}

// Catch and inspect the key
try {
  getUser('');
} catch (err) {
  if (err instanceof ScopeError) {
    console.log(err.key);       // amend:SCO.<loc_b64u>.<msg_b64u>
    console.log(err.timestamp); // 2026-04-08T10:15:00.000Z
  }
}
```

### Decoding a Key

```typescript
import amend from 'amend';

const decoded = amend.engine.decode('amend:VAL.<loc_b64u>.<msg_b64u>');
// Returns a DecodedKey object:
console.log(decoded.errorClass); // 'ValidationError'
console.log(decoded.filePath);   // 'src/services/auth.ts'
console.log(decoded.line);       // 42
console.log(decoded.funcName);   // 'fetchConfig'
console.log(decoded.message);    // 'Configuration URL is required'
```

The `DecodedKey` interface:

```typescript
interface DecodedKey {
  key:        string;
  errorClass: string;
  filePath:   string;
  line:       number;
  funcName:   string;
  message:    string;
}
```

---

## API Reference

### `amend.engine`

The `CoreEngine` namespace — all methods are pure, stateless, and synchronous.

| Method                                   | Returns        | Description                                              |
|------------------------------------------|----------------|----------------------------------------------------------|
| `encode(filePath, line, className, funcName, message, errorClass)` | `string` | Build a self-decoding `amend:` key from raw components |
| `decode(key)`                            | `DecodedKey`   | Fully decode a key back to all its original fields. Throws on invalid input. |
| `verify(key)`                            | `boolean`      | Return `true` if the key is structurally valid           |
| `errorClassFrom(key)`                    | `string`       | Fast extraction of the error class without full decode   |
| `locationFrom(key)`                      | `{ filePath, line, funcName }` | Fast extraction of location fields only  |
| `messageFrom(key)`                       | `string`       | Fast extraction of the message only                      |

### `amend.registry`

The `Registry` singleton manages the local `~/.amend/errors.log` NDJSON file.

| Method                                   | Returns              | Description                                              |
|------------------------------------------|----------------------|----------------------------------------------------------|
| `getAll()`                               | `ErrorRecord[]`      | Read and consolidate all log entries, deduplicated by key. Each record includes an occurrence `count`. |
| `find(key)`                              | `ErrorRecord[]`      | Filter records whose key equals or starts with the given query. |
| `status()`                               | `RegistryStatus`     | Returns `{ total: number, recent: ErrorRecord[] }` (last 5 entries). |
| `clear()`                                | `void`               | Truncate the log file. Prompts for confirmation in the CLI. |
| `exportTo(filePath, format)`             | `void`               | Write all records to a file. `format` is `'json'` or `'log'`. |

The `ErrorRecord` structure returned by registry reads:

```typescript
interface ErrorRecord {
  key:        string;
  errorClass: string;
  message:    string;
  filePath:   string;
  line:       number;
  funcName:   string;
  timestamp:  string;   // most recent occurrence
  count:      number;   // total occurrences
  context?:   string;
  metadata:   Record<string, unknown>[];
}
```

### `amend.ai`

The `AgentConfig` singleton for controlling which file paths are visible to AI agents and for attaching human-authored hints to specific keys.

| Method                          | Description                                                         |
|---------------------------------|---------------------------------------------------------------------|
| `enable({ scope })`             | Enable AI handling for errors originating from the given path prefix |
| `disable({ scope })`            | Disable AI handling for errors from the given path prefix           |
| `hints.set(key, hint)`          | Attach a hint string to a specific `amend:` key                     |
| `hints.get(key)`                | Retrieve the hint for a key. Returns `undefined` if not set.        |
| `hints.clear(key)`              | Remove the hint for a key                                           |

Scope resolution rules: if disabled scopes are matched first, the path is excluded regardless of enabled scopes. If no enabled scopes are defined, all paths are considered enabled by default.

```typescript
import amend from 'amend';

// Only surface errors from the payments module to the AI agent
amend.ai.enable({ scope: 'src/payments' });

// Suppress noisy test infrastructure errors
amend.ai.disable({ scope: 'src/mocks' });

// Attach a fix hint to a known recurring error
amend.ai.hints.set(
  'amend:NET.<loc_b64u>.<msg_b64u>',
  'This timeout occurs when the upstream service is rate-limiting. Increase retry backoff to 2s.'
);
```

---

## CLI Reference

The `amend` binary is registered automatically after installation. All commands operate on the local `~/.amend/errors.log` registry.

### `amend drawErrors`

List all registered errors in a tabular format showing the key and decoded message.

```
amend drawErrors

KEY                                                     MESSAGE
amend:SCO.<loc>.<msg>                                   User ID must be provided
amend:VAL.<loc>.<msg>                                   Configuration URL is required
```

### `amend pin <key>`

Show the full decoded details for a single error by its `amend:` key. If the key is not in the local registry, the command falls back to decoding it directly from the key itself.

```
amend pin "amend:SCO.<loc_b64u>.<msg_b64u>"

[amend pin amend:SCO.<loc_b64u>.<msg_b64u>]

  Message    : User ID must be provided
  ErrorClass : ScopeError
  File       : src/services/user.ts:14
  Function   : getUser
  Timestamp  : 2026-04-08T10:15:00.000Z
  Count      : 3
  Context    : (none)
  Metadata   : (none)
```

### `amend registry [status]`

Show a summary of the registry including total count, recent errors, most common error type, and errors in the last 24 hours.

```
amend registry status

[amend registry status]

  Total errors    : 12
  Recent errors   : 5

  KEY                            MESSAGE                   FILE
  amend:...                      User ID must be provided  src/services/user.ts:14
  ...

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
- `.json` — structured JSON array with all decoded fields
- `.log` — human-readable plain-text format

```bash
amend logRegistry ./reports/errors.json
amend logRegistry ./reports/errors.log
```

---

## Build Scripts

| Script             | Description                                    |
|--------------------|------------------------------------------------|
| `npm run build`    | Compile both ESM and CJS outputs               |
| `npm run build:esm`| Compile ESM output only (`dist/esm/`)          |
| `npm run build:cjs`| Compile CJS output only (`dist/cjs/`)          |
| `npm run test`     | Run the full Vitest test suite once            |
| `npm run test:watch`| Run Vitest in watch mode                      |
| `npm run dev`      | Watch-compile ESM in development mode          |

---

## Module Exports

The package exposes the following named and default exports:

```typescript
// Default export — ergonomic namespace object
import amend from 'amend';
amend.ScopeError
amend.engine.decode(key)
amend.registry.getAll()
amend.ai.enable({ scope })

// Named class exports
import { ScopeError, NetworkError, ValidationError } from 'amend';

// Named module exports for direct use
import { Registry }    from 'amend';
import { CoreEngine }  from 'amend';
import { AgentConfig } from 'amend';
import type { DecodedKey } from 'amend';
```

---

## Registry Storage

The registry file is stored at:

- **Location:** `~/.amend/errors.log` (created automatically on first throw)
- **Format:** Newline-delimited JSON (NDJSON) — one JSON object per line, one line per occurrence
- **Disk record fields:** `key`, `timestamp`, `context` (optional), `metadata` (optional)
- **Message and location are NOT stored on disk** — they are recovered on read by decoding the key via `CoreEngine`

This design keeps the log lean and avoids storing redundant string data for recurring errors.
