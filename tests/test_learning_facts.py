import io
import json
from unittest.mock import Mock
from urllib.error import URLError

import pytest
from django.core.cache.backends.locmem import LocMemCache
from django.urls import reverse

from apps.core import learning_facts as facts


@pytest.fixture
def isolated_facts(monkeypatch):
    backend = LocMemCache("learning-facts-unit-tests", {})
    backend.clear()
    monkeypatch.setattr(facts, "cache", backend)
    yield backend
    backend.clear()


def online_fact(topic="Regenerative braking"):
    return {"id": topic, "title": topic, "text": "A sufficiently detailed educational explanation of energy recovery during vehicle braking.",
            "source_url": "https://en.wikipedia.org/wiki/Regenerative_braking", "source_name": "Wikipedia contributors",
            "mode": "online", "credit": "Wikipedia excerpt", "license_url": facts.LICENSE_URL}


def test_home_never_waits_for_external_facts(client, monkeypatch):
    fetch = Mock(side_effect=AssertionError("Homepage must not fetch"))
    monkeypatch.setattr(facts, "fetch_excerpt", fetch)
    response = client.get(reverse("core:home"))
    assert response.status_code == 200
    assert b"Did you know?" in response.content
    assert response.content.index(b"learning-title") < response.content.index(b"Secure platform access")
    assert b"Source-checked backup fact" in response.content
    fetch.assert_not_called()


def test_public_endpoint_is_safe_and_uncached(client, isolated_facts, monkeypatch):
    fetch = Mock(side_effect=lambda topic: online_fact(topic))
    monkeypatch.setattr(facts, "fetch_excerpt", fetch)
    response = client.get(reverse("core:learning_fact"))
    assert response.status_code == 200
    assert response.json()["mode"] == "online"
    assert "no-store" in response["Cache-Control"]
    assert response["Content-Type"] == "application/json"
    assert client.post(reverse("core:learning_fact")).status_code == 405


def test_shared_cooldown_and_no_recent_repeat(isolated_facts, monkeypatch):
    fetch = Mock(side_effect=lambda topic: online_fact(topic))
    monkeypatch.setattr(facts, "fetch_excerpt", fetch)
    first = facts.random_fact()
    second = facts.random_fact([first["id"]])
    assert second["id"] != first["id"]
    assert fetch.call_count == 1
    isolated_facts.delete(facts.REFRESH_KEY)
    third = facts.random_fact([first["id"], second["id"]])
    assert third["mode"] == "online"
    assert third["id"] not in (first["id"], second["id"])
    assert fetch.call_count == 2


def test_timeout_falls_back_without_repeated_network_calls(isolated_facts, monkeypatch):
    fetch = Mock(side_effect=URLError("offline"))
    monkeypatch.setattr(facts, "fetch_excerpt", fetch)
    first = facts.random_fact()
    second = facts.random_fact([first["id"]])
    assert first["mode"] == second["mode"] == "backup"
    assert first["id"] != second["id"]
    assert fetch.call_count == 1
    assert facts.backup_fact([fact["id"] for fact in facts.BACKUP_FACTS])["id"] != facts.BACKUP_FACTS[-1]["id"]


@pytest.mark.parametrize("payload", [b"not JSON", b"x" * 65537, b'{"type":"disambiguation","extract":"not a model"}', b'{"type":"standard","extract":null}'])
def test_invalid_upstream_excerpts_are_rejected(monkeypatch, payload):
    opener = Mock()
    opener.open.return_value = io.BytesIO(payload)
    monkeypatch.setattr(facts, "build_opener", lambda *args: opener)
    with pytest.raises(ValueError):
        facts.fetch_excerpt("Regenerative braking")


def test_upstream_is_fixed_bounded_plain_text_and_attributed(monkeypatch):
    opener = Mock()
    opener.open.return_value = io.BytesIO(json.dumps({"type": "standard", "extract": "<b>Automotive education</b> " * 100}).encode())
    monkeypatch.setattr(facts, "build_opener", lambda *args: opener)
    fact = facts.fetch_excerpt("Regenerative braking")
    request = opener.open.call_args.args[0]
    assert request.full_url == "https://en.wikipedia.org/api/rest_v1/page/summary/Regenerative_braking"
    assert opener.open.call_args.kwargs["timeout"] == 2
    assert len(fact["text"]) <= 420
    assert "<b>" not in fact["text"]
    assert fact["license_url"] == facts.LICENSE_URL
    assert "shortened" in fact["credit"]
    assert facts.NoRedirects().redirect_request(None, None, 302, "", {}, "http://127.0.0.1/") is None
