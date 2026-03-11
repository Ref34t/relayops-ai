from __future__ import annotations

from fastapi import Header, HTTPException, Request

from app.models import Account


async def get_current_account(
    request: Request,
    x_relayops_api_key: str | None = Header(default=None),
) -> Account:
    repository = request.app.state.repository
    if x_relayops_api_key:
        account = repository.get_account_by_api_key(x_relayops_api_key)
        if not account:
            raise HTTPException(status_code=401, detail="Invalid RelayOps API key.")
        return account
    return repository.get_default_account()
