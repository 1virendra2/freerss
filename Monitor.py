"""
Twitter/X -> Discord Alert System (Free, Unlimited Accounts)
--------------------------------------------------------------
- Reads a list of X/Twitter handles from accounts.txt
- Fetches each account's latest posts via an RSSHub instance
  (RSSHub converts any public X profile into an RSS feed for free)
- Sends BOTH the raw tweet text+link AND an AI-generated short summary
  to a Discord channel via webhook
- Keeps track of already-seen tweets in seen_ids.json so you never
  get duplicate alerts
- Designed to run on a schedule via GitHub Actions (free for public repos)

Required secrets/env vars (set as GitHub Actions secrets):
  DISCORD_WEBHOOK_URL   - your Discord channel webhook URL
  GROQ_API_KEY          - free API key from https://console.groq.com
Optional:
  RSSHUB_BASE           - defaults to https://rsshub.app
                          (self-host your own if the public one gets rate-limited)
"""

import os
import json
import time
import feedparser
import requests

RSSHUB_BASE = os.environ.get("RSSHUB_BASE", "https://rsshub.app")
DISCORD_WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK_URL")
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")

ACCOUNTS_FILE = "accounts.txt"
SEEN_FILE = "seen_ids.json"


def load_accounts():
    if not os.path.exists(ACCOUNTS_FILE):
        return []
    with open(ACCOUNTS_FILE, "r", encoding="utf-8") as f:
        return [
            line.strip().lstrip("@")
            for line in f
            if line.strip() and not line.strip().startswith("#")
        ]


def load_seen():
    if os.path.exists(SEEN_FILE):
        with open(SEEN_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_seen(seen):
    with open(SEEN_FILE, "w", encoding="utf-8") as f:
        json.dump(seen, f, indent=2)


def fetch_feed(handle):
    """Pull latest posts for a handle via RSSHub."""
    url = f"{RSSHUB_BASE}/twitter/user/{handle}"
    try:
        resp = requests.get(url, timeout=20)
        resp.raise_for_status()
        return feedparser.parse(resp.text)
    except Exception as e:
        print(f"[WARN] Could not fetch feed for @{handle}: {e}")
        return None


def summarize(text, handle):
    """Get a short AI summary/brief using Groq's free API."""
    if not GROQ_API_KEY:
        return None
    try:
        resp = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={"Authorization": f"Bearer {GROQ_API_KEY}"},
            json={
                "model": "llama-3.3-70b-versatile",
                "messages": [
                    {
                        "role": "system",
                        "content": (
                            "You summarize a single tweet into one short, "
                            "punchy sentence (max 20 words). No preamble."
                        ),
                    },
                    {"role": "user", "content": f"Tweet by @{handle}: {text}"},
                ],
                "temperature": 0.3,
                "max_tokens": 60,
            },
            timeout=20,
        )
        resp.raise_for_status()
        return resp.json()["choices"][0]["message"]["content"].strip()
    except Exception as e:
        print(f"[WARN] Summary failed: {e}")
        return None


def post_to_discord(handle, raw_text, link, summary):
    if not DISCORD_WEBHOOK_URL:
        print("[ERROR] DISCORD_WEBHOOK_URL not set, skipping post.")
        return

    embed = {
        "title": f"New post from @{handle}",
        "url": link,
        "description": raw_text[:1000],
        "color": 0x1DA1F2,
        "fields": [],
    }
    if summary:
        embed["fields"].append({"name": "Brief", "value": summary})

    payload = {"embeds": [embed]}
    try:
        r = requests.post(DISCORD_WEBHOOK_URL, json=payload, timeout=15)
        r.raise_for_status()
    except Exception as e:
        print(f"[ERROR] Discord post failed for @{handle}: {e}")


def main():
    accounts = load_accounts()
    if not accounts:
        print("No accounts configured in accounts.txt. Add some handles first.")
        return

    seen = load_seen()

    for handle in accounts:
        feed = fetch_feed(handle)
        if not feed or not feed.entries:
            continue

        seen_ids = set(seen.get(handle, []))
        new_ids = []

        # Process oldest-first so Discord shows them in chronological order
        for entry in reversed(feed.entries):
            entry_id = entry.get("id") or entry.get("link")
            if entry_id in seen_ids:
                continue

            raw_text = entry.get("title") or entry.get("summary", "")
            link = entry.get("link", "")

            summary = summarize(raw_text, handle)
            post_to_discord(handle, raw_text, link, summary)

            new_ids.append(entry_id)
            time.sleep(1)  # be gentle with rate limits

        if new_ids:
            seen[handle] = list(seen_ids | set(new_ids))[-200:]  # cap stored history

    save_seen(seen)


if __name__ == "__main__":
    main()

