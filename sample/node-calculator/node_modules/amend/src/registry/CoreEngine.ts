// ── CoreEngine — Amend Self-Decoding Key System ───────────────────────
// Key format:  amend:{CLASS}.{loc_b64u}.{msg_b64u}
//
// Segments (split on "."):
//   CLASS     — 3-char plain-text error code  (SCO / NET / VAL / ERR)
//   loc_b64u  — Base64url of "{filePath}|{line}|{funcName}"
//   msg_b64u  — Base64url of the error message
//
// Decode is a pure stdlib operation: split → Buffer.from → split.
// No keystore, no external state. Fully self-contained.

const ENCODE: Record<string, string> = {
  ScopeError:      'SCO',
  NetworkError:    'NET',
  ValidationError: 'VAL',
};

const DECODE: Record<string, string> = Object.fromEntries(
  Object.entries(ENCODE).map(([k, v]) => [v, k])
);

// ── Internal helpers ──────────────────────────────────────────────────

function b64uEnc(text: string): string {
  return Buffer.from(text, 'utf8').toString('base64url');
}

function b64uDec(token: string): string {
  return Buffer.from(token, 'base64url').toString('utf8');
}

// ── Public types ──────────────────────────────────────────────────────

export interface DecodedKey {
  key:        string;
  errorClass: string;
  filePath:   string;
  line:       number;
  funcName:   string;
  message:    string;
}

// ── Public API ────────────────────────────────────────────────────────

/**
 * Build a self-decoding Amend key.
 *
 * Returns: `"amend:{CLASS}.{loc_b64u}.{msg_b64u}"`
 *
 * Properties:
 *   - Deterministic: same inputs → same key, always.
 *   - Reversible: decode() recovers all original fields.
 *   - Fast: 4 string ops, 2 Buffer calls, zero heap growth.
 */
export function encode(
  filePath:   string,
  line:       number,
  className:  string,
  funcName:   string,
  message:    string,
  errorClass: string,
): string {
  const code   = ENCODE[errorClass] ?? 'ERR';
  const locB64 = b64uEnc(`${filePath}|${line}|${funcName}`);
  const msgB64 = b64uEnc(message);
  return `amend:${code}.${locB64}.${msgB64}`;
}

/**
 * Decode an Amend key back to its original components.
 *
 * @throws {Error} if key does not match the amend: format.
 */
export function decode(key: string): DecodedKey {
  if (!key.startsWith('amend:')) {
    throw new Error(`Invalid amend key (missing prefix): ${key}`);
  }

  const body  = key.slice(6); // strip "amend:"
  const parts = body.split('.') as [string, string, string];

  if (parts.length !== 3) {
    throw new Error(
      `Invalid amend key (expected 3 dot-separated segments after prefix): ${key}`
    );
  }

  const [code, locB64, msgB64] = parts;
  const errorClass = DECODE[code] ?? code;

  const locRaw  = b64uDec(locB64);
  const locParts = locRaw.split('|');

  const filePath = locParts[0] ?? '';
  const line     = parseInt(locParts[1] ?? '0', 10);
  const funcName = locParts[2] ?? '';
  const message  = b64uDec(msgB64);

  return { key, errorClass, filePath, line, funcName, message };
}

/**
 * Return true if key is a structurally valid amend: key.
 */
export function verify(key: string): boolean {
  try {
    const result = decode(key);
    return result.filePath !== undefined;
  } catch {
    return false;
  }
}

// ── AI agent helpers ──────────────────────────────────────────────────

/** Fast extract of errorClass without full decode. */
export function errorClassFrom(key: string): string {
  if (!key.startsWith('amend:')) return 'ERR';
  const code = key.slice(6).split('.')[0];
  return DECODE[code] ?? code;
}

/** Fast extract of location fields only (filePath, line, funcName). */
export function locationFrom(key: string): Pick<DecodedKey, 'filePath' | 'line' | 'funcName'> {
  const { filePath, line, funcName } = decode(key);
  return { filePath, line, funcName };
}

/** Fast extract of message only. */
export function messageFrom(key: string): string {
  return decode(key).message;
}

// ── Namespace export for ergonomic import ─────────────────────────────
export const CoreEngine = {
  encode,
  decode,
  verify,
  errorClassFrom,
  locationFrom,
  messageFrom,
};
