"""Project-wide runtime switches, read from the environment once at import.

Enabling a feature is a deployment decision, so none of these needs a code change.
"""
import os


def _env_flag(name: str, default: bool) -> bool:
    value = os.environ.get(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


# Off: there is no API budget, and a 4-5 minute CPU render per request is too slow
# for a live demo. tools/generate_animation.py explains what would change to enable it.
ENABLE_RUNTIME_GENERATION = _env_flag("ENABLE_RUNTIME_GENERATION", default=False)
