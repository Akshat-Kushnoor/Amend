# ── amend clean registry ─────────────────────────────────────────────
# Truncates ~/.amend/errors.log with confirmation prompt.

from amend.registry.registry import Registry


def clean_registry(target: str = 'registry') -> None:
    if target != 'registry':
        print(f'Unknown target: {target}. Did you mean "amend clean registry"?')
        return

    answer = input('Are you sure you want to clear the entire registry? [y/N] ')

    if answer.strip().lower() in ('y', 'yes'):
        Registry.get_instance().clear()
        print('Registry cleared.')
    else:
        print('Aborted.')
