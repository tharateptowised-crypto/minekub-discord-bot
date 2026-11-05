"""Publish the latest verified Minecraft Survival update to MINEKUB Discord."""
import json
import os
import re
import sys
import time
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen

API = "https://discord.com/api/v10"
TOKEN = os.environ.get("DISCORD_BOT_TOKEN", "").strip()
GUILD_ID = os.environ.get("DISCORD_GUILD_ID", "").strip()
DRY_RUN = os.environ.get("DRY_RUN", "true").strip().lower() != "false"
NEWS_FILE = Path("content/survival-news.json")
HEADLINE = "📣 MINEKUB | ข่าว Minecraft Survival"

def api(method, path, payload=None):
    data = None if payload is None else json.dumps(payload, ensure_ascii=False).encode("utf-8")
    headers = {
        "Authorization": "Bot " + TOKEN,
        "User-Agent": "MINEKUB-NewsPublisher/1.0",
    }
    if payload is not None:
        headers["Content-Type"] = "application/json"
    for attempt in range(4):
        try:
            req = Request(API + path, data=data, headers=headers, method=method)
            with urlopen(req, timeout=25) as response:
                raw = response.read()
                return json.loads(raw.decode("utf-8")) if raw else None
        except HTTPError as error:
            raw = error.read().decode("utf-8", errors="replace")
            if error.code == 429 and attempt < 3:
                try:
                    delay = min(30, float(json.loads(raw).get("retry_after", 2)))
                except (ValueError, TypeError):
                    delay = 2
                time.sleep(max(delay, 1))
                continue
            raise RuntimeError(f"Discord API {method} {path} failed: HTTP {error.code}: {raw[:400]}") from None
    raise RuntimeError("Discord rate-limit retry limit reached")

def normalize(name):
    return re.sub(r"[^a-z0-9ก-๙]", "", name.casefold())

def target_channel(channels):
    text_channels = [c for c in channels if c.get("type") == 0]
    for desired in ("เอาชีวิตรอด", "survival"):
        matches = [c for c in text_channels if normalize(c["name"]) == normalize(desired)]
        if len(matches) == 1:
            return matches[0]
        if len(matches) > 1:
            raise RuntimeError(f"Found more than one matching channel for {desired!r}; no message sent")
    raise RuntimeError("Cannot find #เอาชีวิตรอด / #survival text channel; no message sent")

def main():
    if not TOKEN or not GUILD_ID.isdigit():
        sys.exit("DISCORD_BOT_TOKEN or DISCORD_GUILD_ID is missing/invalid")
    content_data = json.loads(NEWS_FILE.read_text(encoding="utf-8"))
    message = content_data["message"].strip()
    if not message.startswith(HEADLINE):
        sys.exit("News message heading does not match MINEKUB")
    if len(message) > 2000:
        sys.exit(f"Discord message too long ({len(message)} characters)")
    guild = api("GET", f"/guilds/{GUILD_ID}")
    if guild.get("name", "").strip().casefold() != "minekub":
        sys.exit("Server name mismatch; only MINEKUB is allowed")
    me = api("GET", "/users/@me")
    channel = target_channel(api("GET", f"/guilds/{GUILD_ID}/channels"))
    print(f"Validated server: {guild['name']} | channel: #{channel['name']} | dry_run={DRY_RUN}")
    previous = api("GET", f"/channels/{channel['id']}/messages?limit=100")
    own = next((m for m in previous if str(m.get("author", {}).get("id")) == str(me["id"])
                and (m.get("content") or "").startswith(HEADLINE)), None)
    if own and own.get("content") == message:
        print("Already published this exact news update. Nothing changed.")
        return
    if DRY_RUN:
        print("DRY RUN: would " + ("update prior bot message" if own else "post a new message"))
        print(message)
        return
    payload = {"content": message, "allowed_mentions": {"parse": []}}
    if own:
        api("PATCH", f"/channels/{channel['id']}/messages/{own['id']}", payload)
        print("Updated previous MINEKUB Bot Survival news message.")
    else:
        api("POST", f"/channels/{channel['id']}/messages", payload)
        print("Published MINEKUB Survival news message.")

if __name__ == "__main__":
    main()
