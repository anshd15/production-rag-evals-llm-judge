"""Who is asking, and how many answers they have left.

The demo is public because a reviewer should be able to try it in ten seconds.
It also calls a paid model on every message, so "public" cannot mean "unlimited".
The compromise: a few free messages with no sign-in at all, then Google sign-in
for more.

The free allowance is deliberately generous enough for the visitor this exists
for — someone trying three or four tweets — and small enough that a script gets
nothing useful out of it.

Counting anonymous use is the interesting part. A cookie alone resets when the
caller clears it, which a bot does for free; an IP alone punishes everyone behind
one office NAT. So both are counted and the LARGER wins: clearing cookies does
not help, and a shared IP only matters once that IP has really spent the
allowance. Neither signal is trustworthy alone, and neither has to be.
"""
import base64
import hashlib
import hmac
import json
import os
import time
import uuid
from dataclasses import dataclass

ANON_FREE = int(os.getenv("ANON_FREE_MESSAGES", "3"))
USER_DAILY = int(os.getenv("USER_DAILY_MESSAGES", "30"))
COOKIE = "rag_sess"
# Signing key. Generated per process when unset, which logs everyone out on a
# restart -- acceptable for a demo, and far better than a constant baked into a
# public repo where anyone could mint themselves a session.
SECRET = os.getenv("SESSION_SECRET", "").encode() or uuid.uuid4().bytes


class AuthError(RuntimeError):
    """The presented Google credential is not usable."""


def _b64(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).decode().rstrip("=")


def _unb64(txt: str) -> bytes:
    return base64.urlsafe_b64decode(txt + "=" * (-len(txt) % 4))


def sign(payload: dict) -> str:
    """A tamper-evident cookie value. Not encrypted: it holds no secrets."""
    body = _b64(json.dumps(payload, separators=(",", ":")).encode())
    mac = _b64(hmac.new(SECRET, body.encode(), hashlib.sha256).digest())
    return f"{body}.{mac}"


def unsign(value: str) -> dict | None:
    """Returns the payload, or None if it was absent, malformed or edited."""
    try:
        body, mac = value.split(".", 1)
        expected = _b64(hmac.new(SECRET, body.encode(), hashlib.sha256).digest())
        # compare_digest, not ==: a timing comparison leaks the signature byte by byte.
        if not hmac.compare_digest(mac, expected):
            return None
        return json.loads(_unb64(body))
    except Exception:
        return None


def verify_google_credential(credential: str) -> dict:
    """Verify a Google ID token server-side and return the claims we keep.

    The browser hands us a token the browser was given, so it proves nothing
    until Google's signature is checked here. google-auth fetches and caches
    Google's public keys and validates signature, audience, issuer and expiry.
    """
    client_id = os.getenv("GOOGLE_CLIENT_ID", "").strip()
    if not client_id:
        raise AuthError("sign-in is not configured on this deployment")
    try:
        from google.auth.transport import requests as ga_requests
        from google.oauth2 import id_token
        claims = id_token.verify_oauth2_token(credential, ga_requests.Request(), client_id)
    except Exception as exc:
        raise AuthError(f"could not verify that sign-in: {type(exc).__name__}") from exc
    if claims.get("iss") not in ("accounts.google.com", "https://accounts.google.com"):
        raise AuthError("unexpected token issuer")
    return {"sub": claims["sub"], "email": claims.get("email", ""),
            "name": claims.get("name", ""), "picture": claims.get("picture", "")}


@dataclass
class Identity:
    kind: str           # "anon" | "user"
    key: str            # anon id, or the Google subject id
    email: str = ""
    name: str = ""

    @property
    def limit(self) -> int:
        return USER_DAILY if self.kind == "user" else ANON_FREE


# usage[(scope, key, day)] -> count. Per process, which is coherent because the
# service runs a single instance; a multi-instance deployment needs a shared
# store and the README says so rather than pretending otherwise.
_usage: dict[tuple[str, str, str], int] = {}


def _today() -> str:
    return time.strftime("%Y-%m-%d", time.gmtime())


def used(ident: Identity, ip: str) -> int:
    """Anonymous use counts cookie AND ip, and the larger wins.

    Clearing cookies therefore buys nothing, while a signed-in user is counted
    only as themselves — having identified themselves, they should not inherit
    the spending of everyone else behind their router.
    """
    day = _today()
    by_key = _usage.get((ident.kind, ident.key, day), 0)
    if ident.kind == "user":
        return by_key
    return max(by_key, _usage.get(("ip", ip, day), 0))


def charge(ident: Identity, ip: str) -> None:
    day = _today()
    _usage[(ident.kind, ident.key, day)] = _usage.get((ident.kind, ident.key, day), 0) + 1
    if ident.kind == "anon":
        _usage[("ip", ip, day)] = _usage.get(("ip", ip, day), 0) + 1


def identity_from_cookie(raw: str | None) -> tuple[Identity, bool]:
    """Returns (identity, is_new). A new anonymous identity needs a Set-Cookie."""
    data = unsign(raw) if raw else None
    if data and data.get("sub"):
        return Identity("user", data["sub"], data.get("email", ""), data.get("name", "")), False
    if data and data.get("anon"):
        return Identity("anon", data["anon"]), False
    return Identity("anon", uuid.uuid4().hex), True


def cookie_for(ident: Identity) -> str:
    payload = ({"sub": ident.key, "email": ident.email, "name": ident.name}
               if ident.kind == "user" else {"anon": ident.key})
    return sign(payload)


def status(ident: Identity, ip: str) -> dict:
    spent = used(ident, ip)
    return {"signed_in": ident.kind == "user", "email": ident.email, "name": ident.name,
            "used": spent, "limit": ident.limit, "remaining": max(0, ident.limit - spent),
            "sign_in_available": bool(os.getenv("GOOGLE_CLIENT_ID", "").strip())}
