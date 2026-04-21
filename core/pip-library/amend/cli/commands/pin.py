# ── amend pin <key> ──────────────────────────────────────────────────
# Shows full decoded details for an error by its amend: key.

import json
from amend.registry.registry import Registry
from amend.registry.core_engine import decode as engine_decode


def pin(key_input: str) -> None:
    # Allow passing with or without "amend:" prefix
    clean_key = key_input.lstrip('-')
    search_key = clean_key if clean_key.startswith('amend:') else f'amend:{clean_key}'
    
    matches = Registry.get_instance().find(search_key)

    if not matches:
        # Fallback: try to decode the key directly without a registry entry
        try:
            decoded = engine_decode(search_key)
            print(f'[amend pin {search_key}]  (not in local registry)\n')
            print(f'  Message    : {decoded["message"]}')
            print(f'  ErrorClass : {decoded["errorClass"]}')
            print(f'  File       : {decoded["filePath"]}:{decoded["line"]}')
            print(f'  Function   : {decoded["funcName"]}')
        except Exception:
            print(f'No error found for key: {clean_key}')
        return

    # Use the most recent consolidated record
    r = matches[-1]

    print(f'[amend pin {r.key}]\n')
    print(f'  Message    : {r.message}')
    print(f'  ErrorClass : {r.error_class}')
    print(f'  File       : {r.file_path}:{r.line}')
    print(f'  Function   : {r.func_name}')
    print(f'  Timestamp  : {r.timestamp}')
    print(f'  Count      : {r.count}')
    print(f'  Context    : {r.context or "(none)"}')
    metadata_str = json.dumps(r.metadata, indent=4) if r.metadata else '(none)'
    print(f'  Metadata   : {metadata_str}')
