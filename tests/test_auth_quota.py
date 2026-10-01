import pytest

from src import auth
from src.auth import Identity


@pytest.fixture(autouse=True)
def clean_usage():
    auth._usage.clear()
    yield
    auth._usage.clear()


def test_a_tampered_cookie_is_rejected():
    """The cookie is signed, not encrypted: readable, but not editable."""
    good = auth.sign({"sub": "user-1", "email": "a@b.c"})
    assert auth.unsign(good)["sub"] == "user-1"

    body, mac = good.split(".", 1)
    assert auth.unsign(f"{body}x.{mac}") is None      # payload edited
    assert auth.unsign(f"{body}.{mac[:-1]}z") is None  # signature edited
    assert auth.unsign("not-a-cookie") is None
    assert auth.unsign("") is None


def test_promoting_yourself_to_a_user_requires_the_signature():
    """The whole point: an anonymous visitor cannot mint a signed-in session."""
    forged = auth._b64(b'{"sub":"someone-else"}') + ".deadbeef"
    ident, _ = auth.identity_from_cookie(forged)
    assert ident.kind == "anon"


def test_clearing_cookies_does_not_restore_the_free_allowance():
    """A cookie alone is worthless as a counter -- a bot drops it for free, so the
    IP is counted too and the larger of the two wins."""
    first, _ = auth.identity_from_cookie(None)
    for _ in range(auth.ANON_FREE):
        auth.charge(first, "203.0.113.9")
    assert auth.used(first, "203.0.113.9") >= auth.ANON_FREE

    fresh, is_new = auth.identity_from_cookie(None)   # cookies cleared
    assert is_new and fresh.key != first.key
    assert auth.used(fresh, "203.0.113.9") >= auth.ANON_FREE  # still spent


def test_a_signed_in_user_is_not_charged_for_their_neighbours():
    """Shared IPs are real (offices, phone networks). Once someone identifies
    themselves they are counted as themselves, not as their router."""
    ip = "198.51.100.4"
    anon, _ = auth.identity_from_cookie(None)
    for _ in range(auth.ANON_FREE):
        auth.charge(anon, ip)

    user = Identity("user", "google-sub-1", "a@b.c", "A")
    assert auth.used(user, ip) == 0
    assert user.limit == auth.USER_DAILY > auth.ANON_FREE


def test_status_reports_what_the_page_needs_to_say():
    ident, _ = auth.identity_from_cookie(None)
    before = auth.status(ident, "192.0.2.1")
    assert before["remaining"] == auth.ANON_FREE and before["signed_in"] is False

    auth.charge(ident, "192.0.2.1")
    assert auth.status(ident, "192.0.2.1")["remaining"] == auth.ANON_FREE - 1


def test_sign_in_is_refused_when_the_deployment_has_no_client_id(monkeypatch):
    """Better a clear refusal than verifying against an empty audience."""
    monkeypatch.setenv("GOOGLE_CLIENT_ID", "")
    with pytest.raises(auth.AuthError, match="not configured"):
        auth.verify_google_credential("whatever")


def test_an_unverifiable_credential_never_becomes_a_session(monkeypatch):
    """The browser hands us a token the browser was given; it proves nothing
    until Google's signature is checked here."""
    monkeypatch.setenv("GOOGLE_CLIENT_ID", "123.apps.googleusercontent.com")
    with pytest.raises(auth.AuthError, match="could not verify"):
        auth.verify_google_credential("clearly.not.a.jwt")


def test_triage_is_blocked_once_the_allowance_is_spent():
    """End to end: the wall must stop the request BEFORE it reaches the model,
    otherwise the quota protects nothing that costs money."""
    from fastapi.testclient import TestClient

    from src.service import app
    client = TestClient(app)

    me = client.get("/auth/me").json()
    assert me["signed_in"] is False and me["remaining"] == auth.ANON_FREE

    ident, _ = auth.identity_from_cookie(client.cookies.get(auth.COOKIE))
    for _ in range(auth.ANON_FREE):
        auth.charge(ident, "testclient")

    r = client.post("/triage", json={"text": "hello", "context": []})
    assert r.status_code == 402
    detail = r.json()["detail"]
    assert detail["remaining"] == 0 and "Sign in" in detail["error"]
