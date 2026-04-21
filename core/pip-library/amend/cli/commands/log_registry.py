# ── amend logRegistry <filepath> ──────────────────────────────────────
# Exports the full registry to .json or .log format.

from amend.registry.registry import Registry


def log_registry(filepath: str) -> None:
    # Strip leading "--" if user passes --./path style
    clean_path = filepath.lstrip('-')

    if clean_path.endswith('.json'):
        fmt = 'json'
    elif clean_path.endswith('.log'):
        fmt = 'log'
    else:
        print('Unsupported file extension. Use .json or .log')
        return

    Registry.get_instance().export_to(clean_path, fmt)
    print(f'Registry exported to {clean_path} ({fmt} format)')
