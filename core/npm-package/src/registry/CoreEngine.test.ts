/**
 * CoreEngine Tests — encode / decode / verify round-trip
 * Mirrors the Python test suite for cross-language parity.
 */
import { describe, it, expect } from 'vitest';
import {
  encode, decode, verify,
  errorClassFrom, locationFrom, messageFrom,
  CoreEngine,
} from '../registry/CoreEngine.js';

const PARAMS = [
  'src/auth/handler.ts', 12, 'AuthHandler', 'login', 'user not found', 'ScopeError',
] as const;

// ── Basic encode ──────────────────────────────────────────────────────

describe('encode — basic', () => {
  it('returns a string', () => {
    expect(typeof encode(...PARAMS)).toBe('string');
  });

  it('starts with amend: prefix', () => {
    expect(encode(...PARAMS).startsWith('amend:')).toBe(true);
  });

  it('has exactly 3 dot-separated segments after prefix', () => {
    const body  = encode(...PARAMS).slice(6);
    const parts = body.split('.');
    expect(parts).toHaveLength(3);
  });

  it('uses SCO code for ScopeError', () => {
    const key  = encode('f.ts', 1, '', 'fn', 'msg', 'ScopeError');
    const code = key.slice(6).split('.')[0];
    expect(code).toBe('SCO');
  });

  it('uses NET code for NetworkError', () => {
    const key  = encode('f.ts', 1, '', 'fn', 'msg', 'NetworkError');
    const code = key.slice(6).split('.')[0];
    expect(code).toBe('NET');
  });

  it('uses VAL code for ValidationError', () => {
    const key  = encode('f.ts', 1, '', 'fn', 'msg', 'ValidationError');
    const code = key.slice(6).split('.')[0];
    expect(code).toBe('VAL');
  });

  it('falls back to ERR for unknown error class', () => {
    const key  = encode('f.ts', 1, '', 'fn', 'msg', 'CustomError');
    const code = key.slice(6).split('.')[0];
    expect(code).toBe('ERR');
  });

  it('handles empty params without throwing', () => {
    const key = encode('', 0, '', '', '', '');
    expect(key.startsWith('amend:')).toBe(true);
    expect(key.slice(6).split('.')).toHaveLength(3);
  });
});

// ── Decode ────────────────────────────────────────────────────────────

describe('decode — field extraction', () => {
  it('returns all expected fields', () => {
    const key    = encode(...PARAMS);
    const result = decode(key);
    for (const f of ['key', 'errorClass', 'filePath', 'line', 'funcName', 'message']) {
      expect(result).toHaveProperty(f);
    }
  });

  it('key field matches input', () => {
    const key = encode(...PARAMS);
    expect(decode(key).key).toBe(key);
  });

  it('recovers errorClass', () => {
    expect(decode(encode(...PARAMS)).errorClass).toBe('ScopeError');
  });

  it('recovers message', () => {
    expect(decode(encode(...PARAMS)).message).toBe('user not found');
  });

  it('recovers filePath', () => {
    expect(decode(encode(...PARAMS)).filePath).toBe('src/auth/handler.ts');
  });

  it('recovers line number', () => {
    expect(decode(encode(...PARAMS)).line).toBe(12);
  });

  it('recovers funcName', () => {
    expect(decode(encode(...PARAMS)).funcName).toBe('login');
  });

  it('throws on invalid key', () => {
    expect(() => decode('not-a-valid-key')).toThrow();
  });

  it('throws on missing amend: prefix', () => {
    expect(() => decode('SCO.abc.def')).toThrow();
  });
});

// ── Verify ────────────────────────────────────────────────────────────

describe('verify', () => {
  it('returns true for valid key', () => {
    expect(verify(encode(...PARAMS))).toBe(true);
  });

  it('returns false for empty string', () => {
    expect(verify('')).toBe(false);
  });

  it('returns false for garbage string', () => {
    expect(verify('garb@ge!key')).toBe(false);
  });

  it('returns false for partial key', () => {
    expect(verify('amend:SCO.abc')).toBe(false);
  });
});

// ── Determinism ───────────────────────────────────────────────────────

describe('encode — determinism', () => {
  it('same params produce same key across 100 calls', () => {
    const keys = Array.from({ length: 100 }, () => encode(...PARAMS));
    expect(new Set(keys).size).toBe(1);
  });

  it('different params produce different keys', () => {
    const paramSets: Parameters<typeof encode>[] = [
      ['file1.ts', 1, 'C', 'f', 'm', 'ScopeError'],
      ['file2.ts', 1, 'C', 'f', 'm', 'ScopeError'],
      ['file1.ts', 2, 'C', 'f', 'm', 'ScopeError'],
      ['file1.ts', 1, 'C', 'g', 'm', 'ScopeError'],
      ['file1.ts', 1, 'C', 'f', 'n', 'ScopeError'],
      ['file1.ts', 1, 'C', 'f', 'm', 'NetworkError'],
      ['file1.ts', 1, 'C', 'f', 'x', 'ScopeError'],
    ];
    const keys = paramSets.map((p) => encode(...p));
    expect(new Set(keys).size).toBe(paramSets.length);
  });

  it('100 unique errors produce 100 unique keys', () => {
    const keys = Array.from({ length: 100 }, (_, i) =>
      encode(`file${i}.ts`, i, `Class${i}`, `func${i}`, `message ${i}`, 'ScopeError')
    );
    expect(new Set(keys).size).toBe(100);
  });
});

// ── Round-trip ────────────────────────────────────────────────────────

describe('encode → decode round-trip', () => {
  it('recovers all fields exactly', () => {
    const key = encode(...PARAMS);
    const d   = decode(key);
    expect(d.filePath).toBe(PARAMS[0]);
    expect(d.line).toBe(PARAMS[1]);
    expect(d.funcName).toBe(PARAMS[3]);
    expect(d.message).toBe(PARAMS[4]);
    expect(d.errorClass).toBe(PARAMS[5]);
  });

  it('handles unicode message', () => {
    const msg = 'error: 世界🌍';
    const key = encode('a.ts', 1, '', 'fn', msg, 'ScopeError');
    expect(decode(key).message).toBe(msg);
  });

  it('handles long message (200 chars)', () => {
    const msg = 'A'.repeat(200);
    const key = encode('deep/path/module.ts', 999, 'BigClass', 'bigFunc', msg, 'NetworkError');
    const d   = decode(key);
    expect(d.message).toBe(msg);
    expect(d.filePath).toBe('deep/path/module.ts');
    expect(d.line).toBe(999);
  });
});

// ── AI agent helpers ──────────────────────────────────────────────────

describe('AI agent helpers', () => {
  it('errorClassFrom returns errorClass without full decode', () => {
    const key = encode(...PARAMS);
    expect(errorClassFrom(key)).toBe('ScopeError');
  });

  it('locationFrom returns filePath, line, funcName', () => {
    const key = encode(...PARAMS);
    const loc = locationFrom(key);
    expect(loc.filePath).toBe('src/auth/handler.ts');
    expect(loc.line).toBe(12);
    expect(loc.funcName).toBe('login');
  });

  it('messageFrom returns message', () => {
    const key = encode(...PARAMS);
    expect(messageFrom(key)).toBe('user not found');
  });

  it('CoreEngine namespace works identically', () => {
    const key = encode(...PARAMS);
    expect(CoreEngine.decode(key).message).toBe('user not found');
    expect(CoreEngine.verify(key)).toBe(true);
  });
});
