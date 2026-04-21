# ── amend drawErrors ─────────────────────────────────────────────────
# Lists all errors: key + decoded message. Nothing else.

from amend.registry.registry import Registry


def draw_errors() -> None:
    records = Registry.get_instance().get_all()

    if not records:
        print('No errors registered.')
        return

    key_width = 55
    print(f"{'KEY':<{key_width}}MESSAGE")

    for r in records:
        msg = r.message
        print(f"{r.key:<{key_width}}{msg}")
