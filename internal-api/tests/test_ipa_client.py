# tests/test_ipa_client_show_user.py
from pathlib import Path

import pytest
import typer

from config import IPA_CA, IPA_HOST, IPA_PASS, IPA_USER
from lib.ipa_client import IPAClient


@pytest.fixture
def ipa_client() -> IPAClient:
    return IPAClient(
        host=IPA_HOST,
        admin_user=IPA_USER,
        admin_pass=IPA_PASS,
        ca_path=Path(IPA_CA),
    )


def test_show_user_existing(monkeypatch, ipa_client) -> None:  # noqa: ANN001
    """Simulate show_user on an existing user, without asserting sensitive details."""
    monkeypatch.setattr(ipa_client, "login", lambda: None)

    expected_result = {"result": {"uid": ["admin"]}, "value": "admin"}
    monkeypatch.setattr(ipa_client, "call", lambda m, l, k: expected_result)  # noqa: ARG005, E741

    result = ipa_client.show_user("admin")
    assert isinstance(result, dict)
    assert "result" in result
    assert isinstance(result["result"], dict)


def test_show_user_nonexistent(monkeypatch, ipa_client) -> None:  # noqa: ANN001
    """Simulate show_user on a non-existing user."""
    monkeypatch.setattr(ipa_client, "login", lambda: None)

    def fake_call(method, params_list, params_) -> None:  # noqa: ANN001, ARG001
        # Simulate IPA returning an error
        from lib.die import _die  # noqa: PLC0415

        _die("IPA error 4001: vdvdvd: user not found")

    monkeypatch.setattr(ipa_client, "call", fake_call)

    with pytest.raises(typer.Exit) as excinfo:
        ipa_client.show_user("vdvdvd")
    assert excinfo.value.exit_code == 1
