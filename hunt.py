"""
Discord 3-4 char username hunter.
Tries to claim short usernames via Discord API.
Stores attempted names in tried.txt to avoid repeats across runs.
"""

import os
import random
import string
import time
import requests

# ── config ──────────────────────────────────────────────────────────────────
TOKEN       = os.environ["DISCORD_TOKEN"]          # required GitHub secret
TRIED_FILE  = "tried.txt"
CHARS       = string.ascii_lowercase + string.digits  # a-z 0-9
LENGTHS     = [4, 4, 4, 3]   # skew toward 4-char (larger pool, more available)
MAX_TRIES   = 2               # Discord allows ~2 username changes per hour
API_URL     = "https://discord.com/api/v10/users/@me"
# ────────────────────────────────────────────────────────────────────────────


def load_tried() -> set[str]:
    try:
        with open(TRIED_FILE) as f:
            return set(f.read().split())
    except FileNotFoundError:
        return set()


def save_tried(tried: set[str]) -> None:
    with open(TRIED_FILE, "w") as f:
        f.write("\n".join(sorted(tried)) + "\n")


def gen_name(length: int) -> str:
    return "".join(random.choices(CHARS, k=length))


def fresh_candidate(tried: set[str]) -> str | None:
    """Pick a random untried name (up to 1000 attempts)."""
    length = random.choice(LENGTHS)
    for _ in range(1000):
        name = gen_name(length)
        if name not in tried:
            return name
    return None


def try_claim(username: str) -> tuple[int, dict]:
    resp = requests.patch(
        API_URL,
        headers={"Authorization": TOKEN, "Content-Type": "application/json"},
        json={"username": username},
        timeout=15,
    )
    try:
        data = resp.json()
    except Exception:
        data = {}
    return resp.status_code, data


def set_gha_output(key: str, value: str) -> None:
    """Write a key=value pair to GitHub Actions output file (if running in CI)."""
    gha_out = os.environ.get("GITHUB_OUTPUT")
    if gha_out:
        with open(gha_out, "a") as f:
            f.write(f"{key}={value}\n")


def main() -> None:
    tried = load_tried()
    print(f"Previously tried: {len(tried)} names")

    for attempt in range(1, MAX_TRIES + 1):
        name = fresh_candidate(tried)
        if name is None:
            print("Could not find a fresh candidate — tried.txt might be huge.")
            break

        tried.add(name)
        print(f"\n[{attempt}/{MAX_TRIES}] Trying → {name!r}")

        status, data = try_claim(name)

        # ── success ──────────────────────────────────────────────────────────
        if status == 200:
            claimed = data.get("username", name)
            print(f"🎉  SUCCESS — username claimed: {claimed}")
            set_gha_output("claimed", claimed)
            save_tried(tried)
            return

        # ── taken / invalid ───────────────────────────────────────────────
        elif status == 400:
            body_str = str(data).lower()
            if "taken" in body_str or "already" in body_str:
                print(f"  ✗ Taken: {name}")
            else:
                # Could be invalid format or other 400 — log and skip
                errors = data.get("errors", {})
                print(f"  ✗ Rejected ({name}): {errors or data}")

        # ── rate limited ──────────────────────────────────────────────────
        elif status == 429:
            retry_after = data.get("retry_after", 3600)
            print(f"  ⏳ Rate limited — retry after {retry_after}s. Stopping run.")
            save_tried(tried)
            set_gha_output("claimed", "")
            return

        # ── auth error ────────────────────────────────────────────────────
        elif status in (401, 403):
            print(f"  🔑 Auth error {status} — check DISCORD_TOKEN secret is valid.")
            save_tried(tried)
            set_gha_output("claimed", "")
            return

        # ── other ─────────────────────────────────────────────────────────
        else:
            print(f"  ? Unexpected {status}: {data}")

        # Small pause between attempts to be polite
        if attempt < MAX_TRIES:
            time.sleep(3)

    set_gha_output("claimed", "")
    save_tried(tried)
    print(f"\nDone. Total tried so far: {len(tried)}")


if __name__ == "__main__":
    main()
