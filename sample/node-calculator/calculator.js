/**
 * Amend Sample — Terminal Calculator (Node.js)
 * Uses the `amend` npm-package for error management.
 *
 * Setup:
 *   cd sample/node-calculator
 *   npm install
 *   node calculator.js
 */

import amend from 'amend';
import { ScopeError, ValidationError } from 'amend';
import * as readline from 'node:readline';

// ── Operations ────────────────────────────────────────────────────────

function add(a, b) { return a + b; }
function subtract(a, b) { return a - b; }
function multiply(a, b) { return a * b; }

function divide(a, b) {
  if (b === 0) {
    throw new ScopeError('Division by zero is not allowed', {
      context: 'calculator',
      metadata: [{ operation: 'divide', a, b }],
    });
  }
  return a / b;
}

const OPERATIONS = {
  '+': add,
  '-': subtract,
  '*': multiply,
  '/': divide,
};

// ── Input Parsing ─────────────────────────────────────────────────────

function parseNumber(raw, label) {
  const n = Number(raw);
  if (Number.isNaN(n)) {
    throw new ValidationError(`Invalid ${label}: expected a number, got "${raw}"`, {
      context: 'calculator',
      metadata: [{ field: label, received: raw, expected: 'number' }],
    });
  }
  return n;
}

function parseOperator(raw) {
  const op = raw.trim();
  if (!(op in OPERATIONS)) {
    throw new ValidationError(`Unknown operator "${op}". Supported: + - * /`, {
      context: 'calculator',
      metadata: [{ received: op, supported: Object.keys(OPERATIONS) }],
    });
  }
  return op;
}

// ── REPL ──────────────────────────────────────────────────────────────

const BANNER = `
╔══════════════════════════════════════════════════════╗
║          Amend Sample — Terminal Calculator          ║
║          Error management powered by amend           ║
╠══════════════════════════════════════════════════════╣
║  Usage:  <number> <operator> <number>               ║
║  Operators:  +   -   *   /                          ║
║  Commands:   errors  |  status  |  clear  |  quit   ║
╚══════════════════════════════════════════════════════╝
`;

function showErrors() {
  const records = amend.registry.getAll();
  if (!records.length) {
    console.log('  No errors recorded yet.\n');
    return;
  }
  console.log(`\n  ${'KEY'.padEnd(60)} MESSAGE`);
  console.log(`  ${'─'.repeat(60)} ${'─'.repeat(30)}`);
  for (const r of records) {
    console.log(`  ${r.key.padEnd(60)} ${r.message}`);
  }
  console.log();
}

function showStatus() {
  const st = amend.registry.status();
  console.log(`\n  Total errors : ${st.total}`);
  if (st.recent.length) {
    console.log('  Recent:');
    for (const r of st.recent) {
      console.log(`    [${r.errorClass}] ${r.message}  (×${r.count})`);
    }
  }
  console.log();
}

function processLine(raw) {
  const line = raw.trim();
  if (!line) return true;

  const cmd = line.toLowerCase();

  if (['quit', 'exit', 'q'].includes(cmd)) {
    console.log('Goodbye!');
    return false;
  }

  if (cmd === 'errors') { showErrors(); return true; }
  if (cmd === 'status') { showStatus(); return true; }
  if (cmd === 'clear')  { amend.registry.clear(); console.log('  Registry cleared.\n'); return true; }

  // ── Calculation ───────────────────────────────────────
  const parts = line.split(/\s+/);
  if (parts.length !== 3) {
    try {
      throw new ValidationError(`Expected format: <number> <op> <number>, got ${parts.length} parts`, {
        context: 'calculator',
        metadata: [{ raw_input: line, parts: parts.length }],
      });
    } catch (e) {
      console.log(`  ✗ ${e.message}`);
      console.log(`    key: ${e.key}\n`);
      return true;
    }
  }

  try {
    const a  = parseNumber(parts[0], 'first operand');
    const op = parseOperator(parts[1]);
    const b  = parseNumber(parts[2], 'second operand');

    const result = OPERATIONS[op](a, b);
    console.log(`  ✓ ${a} ${op} ${b} = ${result}\n`);
  } catch (e) {
    if (e instanceof ScopeError || e instanceof ValidationError) {
      console.log(`  ✗ ${e.message}`);
      console.log(`    key: ${e.key}\n`);
    } else {
      throw e;
    }
  }

  return true;
}

// ── Entry ─────────────────────────────────────────────────────────────

console.log(BANNER);

const rl = readline.createInterface({
  input:  process.stdin,
  output: process.stdout,
  prompt: 'calc > ',
});

rl.prompt();

rl.on('line', (line) => {
  const keepGoing = processLine(line);
  if (!keepGoing) { rl.close(); return; }
  rl.prompt();
});

rl.on('close', () => {
  console.log('\nGoodbye!');
  process.exit(0);
});
