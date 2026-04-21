# ── amend registry status ────────────────────────────────────────────
# Shows total count, recent 5 errors with file locations, and analytics.

from datetime import datetime, timezone
from amend.registry.registry import Registry


def registry_status(action: str = 'status') -> None:
    if action != 'status':
        print(f'Unknown action: {action}. Did you mean "amend registry status"?')
        return

    reg    = Registry.get_instance()
    status = reg.status()
    total  = status['total']
    recent = status['recent']

    print('[amend registry status]\n')
    print(f'  Total errors    : {total}')
    print(f'  Recent errors   : {len(recent)}\n')

    if recent:
        key_w = 30
        msg_w = 25
        print(f"  {'KEY':<{key_w}}{'MESSAGE':<{msg_w}}FILE")

        for r in recent:
            short_key = r.key[-30:] if len(r.key) > 30 else r.key
            print(f"  {short_key:<{key_w}}{r.message:<{msg_w}}{r.file_path}:{r.line}")

    # ── Basic analytics ──────────────────────────────────────────
    if total > 0:
        all_records = reg.get_all()

        class_count: dict[str, int] = {}
        for r in all_records:
            class_count[r.error_class] = class_count.get(r.error_class, 0) + 1
        top_class = max(class_count.items(), key=lambda x: x[1]) if class_count else None

        now = datetime.now(timezone.utc)
        last_24h = sum(
            1 for r in all_records
            if (now - datetime.fromisoformat(r.timestamp.replace('Z', '+00:00'))).total_seconds() < 86400
        )

        print('\n  Analytics:')
        if top_class:
            print(f'    Most common type  : {top_class[0]} ({top_class[1]}x)')
        print(f'    Last 24h          : {last_24h} errors')
