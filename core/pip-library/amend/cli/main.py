#!/usr/bin/env python3
# ── Amend CLI Entry Point ────────────────────────────────────────────

import argparse
import sys

from amend.cli.commands.draw_errors import draw_errors
from amend.cli.commands.pin import pin
from amend.cli.commands.clean_registry import clean_registry
from amend.cli.commands.registry_status import registry_status
from amend.cli.commands.log_registry import log_registry


def run() -> None:
    parser = argparse.ArgumentParser(
        prog='amend',
        description='Amend — Cross-language error intelligence CLI',
    )
    subparsers = parser.add_subparsers(dest='command')

    # ── drawErrors ───────────────────────────────────────────────
    subparsers.add_parser('drawErrors', help='List all registered errors (hash + message)')

    # ── pin ──────────────────────────────────────────────────────
    pin_parser = subparsers.add_parser('pin', help='Show full details for an error by its hash')
    pin_parser.add_argument('hash', type=str, help='Error hash (e.g. a3f9c-b8e2d-k4p1a)')

    # ── clean ────────────────────────────────────────────────────
    clean_parser = subparsers.add_parser('clean', help='Clear the registry')
    clean_parser.add_argument('target', nargs='?', default='registry', help='What to clean (default: registry)')

    # ── registry ─────────────────────────────────────────────────
    reg_parser = subparsers.add_parser('registry', help='Show registry status')
    reg_parser.add_argument('action', nargs='?', default='status', help='Action (default: status)')

    # ── logRegistry ──────────────────────────────────────────────
    log_parser = subparsers.add_parser('logRegistry', help='Export registry to .json or .log')
    log_parser.add_argument('filepath', type=str, help='Output file path')

    args = parser.parse_args()

    if args.command == 'drawErrors':
        draw_errors()
    elif args.command == 'pin':
        pin(args.hash)
    elif args.command == 'clean':
        clean_registry(args.target)
    elif args.command == 'registry':
        registry_status(args.action)
    elif args.command == 'logRegistry':
        log_registry(args.filepath)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == '__main__':
    run()
