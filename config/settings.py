import os
from dotenv import load_dotenv

load_dotenv()


def _get(key, default=None):
    value = os.getenv(key)
    if value is None:
        return default
    return value.strip()


def _get_bool(key, default="false"):
    value = _get(key, default)
    return str(value).lower() in ("1", "true", "yes", "on")


TOKEN = _get("TOKEN")
PREFIX = _get("PREFIX", "imposter") or "imposter"
SYNC_COMMANDS = _get_bool("SYNC_COMMANDS", "false")
ENV = (_get("ENV", "prod") or "prod").lower()


def is_dev():
    return ENV == "dev"


def validate():
    missing = []

    if not TOKEN:
        missing.append("TOKEN")

    if missing:
        raise RuntimeError(f"Missing env variables: {', '.join(missing)}")
