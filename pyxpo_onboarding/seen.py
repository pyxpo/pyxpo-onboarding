"""Remember that the user finished onboarding, so the app shows it once."""
from __future__ import annotations

from typing import Any, Callable, NamedTuple, Optional

DEFAULT_KEY = "pyxpo.onboarding.seen"


class SeenFlag(NamedTuple):
    seen: bool
    mark_seen: Callable[[], None]
    reset: Callable[[], None]


def use_onboarding_seen(key: str = DEFAULT_KEY, version: Any = None, storage: Optional[Any] = None) -> SeenFlag:
    """`(seen, mark_seen, reset)` backed by pyxpo-storage. Bump `version` to show onboarding again after a
    redesign: each version keeps its own flag. `storage` is a `pyxpo_storage.Storage` instance (default store
    when None)."""
    try:
        from pyxpo_storage import use_storage_boolean
    except ImportError as e:  # pragma: no cover - depends on the install
        raise ImportError("use_onboarding_seen needs pyxpo-storage: pip install 'pyxpo-onboarding[storage]'") from e
    full = key if version is None else "%s.v%s" % (key, version)
    value, set_value = use_storage_boolean(full, storage)
    return SeenFlag(bool(value), lambda: set_value(True), lambda: set_value(None))
