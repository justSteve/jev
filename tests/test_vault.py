import os

import pytest

from jevloop import vault
from jevloop.vault import VaultError, load_environment


@pytest.fixture
def clean_env(monkeypatch):
    for name in (*vault.SECRET_NAMES, vault.SECRETS_POINTER, "DEFAULT_SYMBOL"):
        monkeypatch.delenv(name, raising=False)
    monkeypatch.setattr(vault, "DEFAULT_SECRETS_PATH", vault.Path("/nonexistent/vault/env"))


def _vault_file(tmp_path, text, mode=0o600):
    p = tmp_path / "vault_env"
    p.write_text(text)
    p.chmod(mode)
    return p


def test_vault_values_load_and_retired_names_are_skipped(tmp_path, clean_env):
    v = _vault_file(tmp_path, "ALPACA_API_KEY=PKabc\nALPACA_API_KEY_RETIRED_20260101T000000Z=old\n")
    env = tmp_path / ".env"
    env.write_text(f"JEV_SECRETS_FILE={v}\nDEFAULT_SYMBOL=ETH/USD\n")
    assert load_environment(env) == v
    assert os.environ["ALPACA_API_KEY"] == "PKabc"
    assert os.environ["DEFAULT_SYMBOL"] == "ETH/USD"
    assert "ALPACA_API_KEY_RETIRED_20260101T000000Z" not in os.environ


def test_secret_in_dotenv_is_refused(tmp_path, clean_env):
    env = tmp_path / ".env"
    env.write_text("ALPACA_API_KEY=PKleaked\n")
    with pytest.raises(VaultError):
        load_environment(env)


def test_empty_secret_placeholder_does_not_blank_the_vault(tmp_path, clean_env):
    v = _vault_file(tmp_path, "AI_GATEWAY_API_KEY=gw\n")
    env = tmp_path / ".env"
    env.write_text(f"JEV_SECRETS_FILE={v}\nAI_GATEWAY_API_KEY=\n")
    load_environment(env)
    assert os.environ["AI_GATEWAY_API_KEY"] == "gw"


def test_world_readable_vault_is_refused(tmp_path, clean_env):
    v = _vault_file(tmp_path, "ALPACA_API_KEY=PKabc\n", mode=0o644)
    env = tmp_path / ".env"
    env.write_text(f"JEV_SECRETS_FILE={v}\n")
    with pytest.raises(VaultError):
        load_environment(env)


def test_explicit_pointer_to_missing_file_is_refused(tmp_path, clean_env):
    env = tmp_path / ".env"
    env.write_text(f"JEV_SECRETS_FILE={tmp_path / 'missing'}\n")
    with pytest.raises(VaultError):
        load_environment(env)


def test_no_vault_at_all_returns_none(tmp_path, clean_env):
    env = tmp_path / ".env"
    env.write_text("DEFAULT_SYMBOL=BTC/USD\n")
    assert load_environment(env) is None
