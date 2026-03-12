from __future__ import annotations

import hashlib
import hmac
import os
from datetime import timedelta

from fastapi import Header, HTTPException, Request

from app.config import Settings
from app.models import Account


def hash_password(password: str, salt: str | None = None) -> str:
    actual_salt = salt or os.urandom(16).hex()
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), actual_salt.encode("utf-8"), 120_000)
    return f"{actual_salt}${digest.hex()}"


def verify_password(password: str, password_hash: str | None) -> bool:
    if not password_hash or "$" not in password_hash:
        return False
    salt, _ = password_hash.split("$", 1)
    expected = hash_password(password, salt)
    return hmac.compare_digest(expected, password_hash)


def session_expiry(settings: Settings):
    from app.models import utc_now

    return utc_now() + timedelta(seconds=settings.session_max_age_seconds)


async def get_current_account(
    request: Request,
    x_relayops_api_key: str | None = Header(default=None),
) -> Account:
    repository = request.app.state.repository
    if x_relayops_api_key:
        account = repository.get_account_by_api_key(x_relayops_api_key)
        if not account:
            raise HTTPException(status_code=401, detail="Invalid RelayOps API key.")
        request.state.auth_mode = "api_key"
        return account

    session_id = request.session.get("relayops_session_id")
    if session_id:
        account = repository.get_account_by_session(session_id)
        if account:
            request.state.auth_mode = "session"
            return account
        request.session.pop("relayops_session_id", None)

    raise HTTPException(status_code=401, detail="Authentication required.")


async def get_session_account(request: Request) -> Account:
    repository = request.app.state.repository
    session_id = request.session.get("relayops_session_id")
    if session_id:
        account = repository.get_account_by_session(session_id)
        if account:
            request.state.auth_mode = "session"
            return account
        request.session.pop("relayops_session_id", None)

    raise HTTPException(status_code=401, detail="Session authentication required.")
