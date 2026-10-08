"""Share-link tokens. Only the hash is stored, so a database leak cannot be
replayed into working links; revoking deletes or flags the stored hash."""

from __future__ import annotations

import hashlib
import secrets
from dataclasses import dataclass


@dataclass(frozen=True)
class ShareToken:
    token: str
    token_hash: str


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def new_share_token() -> ShareToken:
    token = secrets.token_urlsafe(24)
    return ShareToken(token=token, token_hash=hash_token(token))
