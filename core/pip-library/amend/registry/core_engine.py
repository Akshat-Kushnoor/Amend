# ── CoreEngine — Amend Self-Decoding Key System ───────────────────────
# Key format:  amend:{CLASS}.{loc_b64u}.{msg_b64u}
#
# Segments (split on "."):
#   CLASS     — 3-char plain-text error code  (SCO / NET / VAL / ERR)
#   loc_b64u  — Base64url of "{filePath}|{line}|{funcName}"
#   msg_b64u  — Base64url of the error message
#
# Decode is a pure stdlib operation: split → b64decode → split.
# No keystore, no external state. Fully self-contained.

import base64

# ── Error class registry ─────────────────────────────────────────────
_ENCODE: dict[str, str] = {
    'ScopeError':      'SCO',
    'NetworkError':    'NET',
    'ValidationError': 'VAL',
}
_DECODE: dict[str, str] = {v: k for k, v in _ENCODE.items()}


# ── Internal helpers ──────────────────────────────────────────────────

def _b64u_enc(text: str) -> str:
    """Encode a UTF-8 string to Base64url with no padding."""
    return base64.urlsafe_b64encode(text.encode('utf-8')).rstrip(b'=').decode('ascii')


def _b64u_dec(token: str) -> str:
    """Decode a Base64url token (with or without padding) to a UTF-8 string."""
    # Re-add padding: length must be a multiple of 4
    pad = (-len(token)) % 4
    return base64.urlsafe_b64decode(token + '=' * pad).decode('utf-8')


# ── Public API ────────────────────────────────────────────────────────

def encode(
    file_path:   str,
    line:        int,
    class_name:  str,
    func_name:   str,
    message:     str,
    error_class: str,
) -> str:
    """
    Build a self-decoding Amend key.

    Returns:
        "amend:{CLASS}.{loc_b64u}.{msg_b64u}"

    Properties:
        - Deterministic: same inputs → same key, always.
        - Reversible: decode() recovers all original fields.
        - Fast: 4 string ops, 3 base64 calls, zero allocations beyond output.
    """
    code    = _ENCODE.get(error_class, 'ERR')
    loc_b64 = _b64u_enc(f'{file_path}|{line}|{func_name}')
    msg_b64 = _b64u_enc(message)
    return f'amend:{code}.{loc_b64}.{msg_b64}'


def decode(key: str) -> dict:
    """
    Decode an Amend key back to its original components.

    Returns a dict with:
        key, errorClass, filePath, line, funcName, message

    Raises:
        ValueError — if the key does not match the amend: format.
    """
    if not key.startswith('amend:'):
        raise ValueError(f'Invalid amend key (missing prefix): {key!r}')

    body = key[6:]  # strip "amend:"
    parts = body.split('.', 2)

    if len(parts) != 3:
        raise ValueError(
            f'Invalid amend key (expected 3 dot-separated segments after prefix): {key!r}'
        )

    code, loc_b64, msg_b64 = parts
    error_class = _DECODE.get(code, code)  # fall back to raw code if unknown

    loc_raw  = _b64u_dec(loc_b64)
    loc_parts = loc_raw.split('|', 2)

    file_path = loc_parts[0] if len(loc_parts) > 0 else ''
    line      = int(loc_parts[1]) if len(loc_parts) > 1 and loc_parts[1].isdigit() else 0
    func_name = loc_parts[2] if len(loc_parts) > 2 else ''
    message   = _b64u_dec(msg_b64)

    return {
        'key':        key,
        'errorClass': error_class,
        'filePath':   file_path,
        'line':       line,
        'funcName':   func_name,
        'message':    message,
    }


def verify(key: str) -> bool:
    """
    Return True if key is a structurally valid amend: key, False otherwise.
    Does not validate the decoded content — only checks format.
    """
    try:
        result = decode(key)
        return bool(result.get('filePath') is not None)
    except (ValueError, Exception):
        return False


# ── Singleton-style namespace for ergonomic import ───────────────────
class CoreEngine:
    """Namespace wrapper — all methods are module-level functions."""
    encode = staticmethod(encode)
    decode = staticmethod(decode)
    verify = staticmethod(verify)

    # AI agent helpers
    @staticmethod
    def error_class(key: str) -> str:
        """Fast extract of errorClass from key without full decode."""
        if not key.startswith('amend:'):
            return 'ERR'
        code = key[6:].split('.', 1)[0]
        return _DECODE.get(code, code)

    @staticmethod
    def location(key: str) -> dict:
        """Fast extract of location fields only (filePath, line, funcName)."""
        d = decode(key)
        return {'filePath': d['filePath'], 'line': d['line'], 'funcName': d['funcName']}

    @staticmethod
    def message(key: str) -> str:
        """Fast extract of message only."""
        return decode(key)['message']
