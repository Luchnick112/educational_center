import json
import time
import urllib.error
import urllib.parse
import urllib.request

from django.conf import settings
from django.core.management.base import BaseCommand

from users.services.telegram_linking import link_user_by_start_token


class Command(BaseCommand):
    help = "Poll Telegram getUpdates and link users on '/start <token>' without webhooks."

    def add_arguments(self, parser):
        parser.add_argument("--once", action="store_true", help="Run one polling iteration and exit.")
        parser.add_argument("--loop", action="store_true", help="Keep polling in a loop (default).")
        parser.add_argument("--drop-pending", action="store_true", help="Discard pending updates before starting.")
        parser.add_argument("--timeout", type=int, default=25, help="Long-poll timeout passed to Telegram, in seconds.")
        parser.add_argument("--sleep", type=float, default=1.0, help="Sleep between iterations, in seconds.")
        parser.add_argument("--limit", type=int, default=50, help="Max updates per request.")

    def _tg_request(self, method: str, params: dict):
        bot_token = (getattr(settings, "TELEGRAM_BOT_TOKEN", "") or "").strip()
        if not bot_token:
            raise RuntimeError("TELEGRAM_BOT_TOKEN is not set")

        qs = urllib.parse.urlencode(params)
        url = f"https://api.telegram.org/bot{bot_token}/{method}?{qs}"
        req = urllib.request.Request(url, headers={"Accept": "application/json"})
        with urllib.request.urlopen(req, timeout=max(5, int(params.get("timeout", 0) or 30) + 10)) as resp:
            body = resp.read().decode("utf-8")
        return json.loads(body)

    def _handle_update(self, update: dict):
        message = update.get("message") or update.get("edited_message") or {}
        text = (message.get("text") or "").strip()
        if not text.startswith("/start"):
            return

        parts = text.split(maxsplit=1)
        if len(parts) != 2:
            return

        token_value = parts[1].strip()
        if not token_value:
            return

        chat = message.get("chat") or {}
        from_user = message.get("from") or {}
        chat_id = chat.get("id")
        telegram_user_id = from_user.get("id")
        telegram_username = (from_user.get("username") or "").strip()

        if chat_id is None or telegram_user_id is None:
            return

        link_user_by_start_token(
            token=token_value,
            chat_id=int(chat_id),
            telegram_user_id=int(telegram_user_id),
            telegram_username=telegram_username,
        )

    def handle(self, *args, **options):
        run_once = bool(options["once"])
        run_loop = bool(options["loop"]) or not run_once
        drop_pending = bool(options["drop_pending"])
        timeout = max(0, int(options["timeout"]))
        sleep_seconds = max(0.0, float(options["sleep"]))
        limit = max(1, int(options["limit"]))

        offset = 0

        if drop_pending:
            try:
                data = self._tg_request("getUpdates", {"offset": 0, "timeout": 0, "limit": limit})
                updates = data.get("result") or []
                for upd in updates:
                    upd_id = upd.get("update_id")
                    if isinstance(upd_id, int) and upd_id >= offset:
                        offset = upd_id + 1
            except Exception:
                # If this fails, continue with offset=0; user can retry later.
                pass

        while True:
            try:
                data = self._tg_request(
                    "getUpdates",
                    {"offset": offset, "timeout": timeout, "limit": limit, "allowed_updates": json.dumps(["message", "edited_message"])},
                )
            except urllib.error.HTTPError as e:
                self.stderr.write(f"Telegram HTTP error: {e.code}")
                if run_once:
                    return
                time.sleep(max(5.0, sleep_seconds))
                continue
            except Exception as e:
                self.stderr.write(f"Telegram polling error: {e}")
                if run_once:
                    return
                time.sleep(max(5.0, sleep_seconds))
                continue

            if not data.get("ok"):
                self.stderr.write("Telegram response not ok")
                if run_once:
                    return
                time.sleep(max(5.0, sleep_seconds))
                continue

            updates = data.get("result") or []
            for upd in updates:
                upd_id = upd.get("update_id")
                if isinstance(upd_id, int) and upd_id >= offset:
                    offset = upd_id + 1
                self._handle_update(upd)

            if run_once:
                return
            if not run_loop:
                return
            time.sleep(sleep_seconds)
