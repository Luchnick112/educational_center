from __future__ import annotations

from dataclasses import dataclass

from django.db import transaction
from django.utils import timezone

from users.models import TelegramLinkToken, User


@dataclass(frozen=True)
class TelegramLinkResult:
    ok: bool
    reason: str = ""


@transaction.atomic
def link_user_by_start_token(
    *,
    token: str,
    chat_id: int,
    telegram_user_id: int,
    telegram_username: str = "",
) -> TelegramLinkResult:
    token = (token or "").strip()
    if not token:
        return TelegramLinkResult(ok=False, reason="missing_token")

    link = TelegramLinkToken.objects.select_related("user").filter(token=token).first()
    if not link or not link.is_active():
        return TelegramLinkResult(ok=False, reason="invalid_or_expired_token")

    # Prevent accidental hijacking: a chat can only be linked to one user.
    existing = User.objects.filter(telegram_chat_id=chat_id).exclude(pk=link.user_id).first()
    if existing:
        return TelegramLinkResult(ok=False, reason="chat_already_linked")

    user = link.user
    user.telegram_chat_id = int(chat_id)
    user.telegram_user_id = int(telegram_user_id)
    user.save(update_fields=["telegram_chat_id", "telegram_user_id"])

    link.used_at = timezone.now()
    link.linked_chat_id = int(chat_id)
    link.linked_user_id = int(telegram_user_id)
    link.linked_username = (telegram_username or "").strip()
    link.save(update_fields=["used_at", "linked_chat_id", "linked_user_id", "linked_username"])

    return TelegramLinkResult(ok=True)

