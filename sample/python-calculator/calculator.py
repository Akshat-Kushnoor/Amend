"""
Amend Sample — Terminal Calculator (Python)
Uses the `amend` pip-library for error management.

Install amend first:
    pip install -e ../../core/pip-library
"""

import sys
from amend import ScopeError, ValidationError
import amend


# ── Operations ────────────────────────────────────────────────────────

def add(a: float, b: float) -> float:
    return a + b


def subtract(a: float, b: float) -> float:
    return a - b


def multiply(a: float, b: float) -> float:
    return a * b


def divide(a: float, b: float) -> float:
    if b == 0:
        raise ScopeError(
            'Division by zero is not allowed',
            context='calculator',
            metadata=[{'operation': 'divide', 'a': a, 'b': b}],
        )
    return a / b


OPERATIONS = {
    '+': add,
    '-': subtract,
    '*': multiply,
    '/': divide,
}


# ── Input Parsing ─────────────────────────────────────────────────────

def parse_number(raw: str, label: str) -> float:
    """Convert a raw string to float, raising ValidationError on failure."""
    try:
        return float(raw)
    except ValueError:
        raise ValidationError(
            f'Invalid {label}: expected a number, got "{raw}"',
            context='calculator',
            metadata=[{'field': label, 'received': raw, 'expected': 'number'}],
        )


def parse_operator(raw: str) -> str:
    """Validate the operator string."""
    op = raw.strip()
    if op not in OPERATIONS:
        raise ValidationError(
            f'Unknown operator "{op}". Supported: + - * /',
            context='calculator',
            metadata=[{'received': op, 'supported': list(OPERATIONS.keys())}],
        )
    return op


# ── REPL ──────────────────────────────────────────────────────────────

BANNER = """
╔══════════════════════════════════════════════════════╗
║          Amend Sample — Terminal Calculator          ║
║          Error management powered by amend           ║
╠══════════════════════════════════════════════════════╣
║  Usage:  <number> <operator> <number>               ║
║  Operators:  +   -   *   /                          ║
║  Commands:   errors  |  status  |  clear  |  quit   ║
╚══════════════════════════════════════════════════════╝
"""


def run():
    print(BANNER)

    while True:
        try:
            raw = input('calc > ').strip()
        except (EOFError, KeyboardInterrupt):
            print('\nGoodbye!')
            break

        if not raw:
            continue

        # ── Meta-commands ─────────────────────────────────────
        cmd = raw.lower()

        if cmd in ('quit', 'exit', 'q'):
            print('Goodbye!')
            break

        if cmd == 'errors':
            records = amend.registry.get_all()
            if not records:
                print('  No errors recorded yet.\n')
            else:
                print(f'\n  {"KEY":<60} {"MESSAGE"}')
                print(f'  {"─" * 60} {"─" * 30}')
                for r in records:
                    print(f'  {r.key:<60} {r.message}')
                print()
            continue

        if cmd == 'status':
            st = amend.registry.status()
            print(f'\n  Total errors : {st["total"]}')
            if st['recent']:
                print(f'  Recent:')
                for r in st['recent']:
                    print(f'    [{r.error_class}] {r.message}  (×{r.count})')
            print()
            continue

        if cmd == 'clear':
            amend.registry.clear()
            print('  Registry cleared.\n')
            continue

        # ── Calculation ───────────────────────────────────────
        parts = raw.split()
        if len(parts) != 3:
            try:
                raise ValidationError(
                    f'Expected format: <number> <op> <number>, got {len(parts)} parts',
                    context='calculator',
                    metadata=[{'raw_input': raw, 'parts': len(parts)}],
                )
            except ValidationError as e:
                print(f'  ✗ {e}')
                print(f'    key: {e.key}\n')
                continue

        try:
            a  = parse_number(parts[0], 'first operand')
            op = parse_operator(parts[1])
            b  = parse_number(parts[2], 'second operand')

            result = OPERATIONS[op](a, b)
            print(f'  ✓ {a} {op} {b} = {result}\n')

        except (ScopeError, ValidationError) as e:
            print(f'  ✗ {e}')
            print(f'    key: {e.key}\n')


if __name__ == '__main__':
    run()
