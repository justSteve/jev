"""Loads settings from .env and secrets from the vault, before anything runs.

Secrets live outside the tree, in the vault file named by JEV_SECRETS_FILE
(default /home/vault/jev/env, mode 0600), written by COO's vault-set.py.
The in-tree .env holds settings (DEFAULT_SYMBOL, ...) and that one pointer,
never a secret value: a non-empty secret found in .env is refused, the same
convention Strader's config loader enforces.

Precedence when a name appears in more than one place:
vault file > .env > process environment.
"""

from __future__ import annotations

import os
import stat
from pathlib import Path

from dotenv import dotenv_values

SKILL_DIR = Path(__file__).resolve().parent.parent
DEFAULT_ENV_PATH = SKILL_DIR / ".env"

SECRETS_POINTER = "JEV_SECRETS_FILE"
DEFAULT_SECRETS_PATH = Path("/home/vault/jev/env")

SECRET_NAMES = (
    "ALPACA_API_KEY",
    "ALPACA_SECRET_KEY",
    "AI_GATEWAY_API_KEY",
    "TYPESAFE_API_KEY",
)


class VaultError(Exception):
    pass


def resolve_secrets_path(dotenv: dict, environ: dict) -> tuple[Path | None, bool]:
    """(path, explicit). An explicit pointer must exist; the default path is
    used only when present. (None, False) means no secrets file at all."""
    raw = dotenv.get(SECRETS_POINTER) or environ.get(SECRETS_POINTER)
    if raw:
        return Path(raw).expanduser(), True
    if DEFAULT_SECRETS_PATH.exists():
        return DEFAULT_SECRETS_PATH, False
    return None, False


def secrets_file_problem(path: Path) -> str | None:
    if not path.exists():
        return f"{SECRETS_POINTER}: {path} does not exist"
    mode = stat.S_IMODE(path.stat().st_mode)
    if mode & 0o077:
        return f"{SECRETS_POINTER}: {path} is mode {mode:04o}; a secrets file must be 0600"
    return None


def load_environment(env_path: Path = DEFAULT_ENV_PATH) -> Path | None:
    """Populate os.environ from .env, then from the vault. Returns the vault
    path used, or None if there is none (the loop then runs without keys:
    the mock decision client, and a clear refusal from Alpaca setup)."""
    dotenv = {k: v for k, v in dotenv_values(env_path).items() if v is not None} if env_path.exists() else {}

    leaked = [name for name in SECRET_NAMES if dotenv.get(name, "").strip()]
    if leaked:
        raise VaultError(
            f"refusing to start: {', '.join(leaked)} set in {env_path}. Secrets live in the "
            f"vault, not .env: move them with "
            "/root/projects/COO/factory/scripts/vault-set.py jev <NAME>, then delete the line."
        )

    for key, value in dotenv.items():
        if key in SECRET_NAMES:
            continue  # an empty placeholder must not blank out a real value
        os.environ[key] = value

    path, explicit = resolve_secrets_path(dotenv, dict(os.environ))
    if path is None:
        return None
    problem = secrets_file_problem(path)
    if problem:
        raise VaultError(problem)

    for key, value in dotenv_values(path).items():
        if value is None or "_RETIRED_" in key:
            continue
        os.environ[key] = value
    return path
