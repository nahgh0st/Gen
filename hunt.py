"""
Discord 3-char username hunter — systematic queue approach.

First run:  generates all 46,656 possible 3-char [a-z0-9] names,
            shuffles them, saves to queue.txt
Every run:  pops 2 names off the queue, tries to claim each one.
            If claimed → writes claimed.txt, workflow opens a GitHub Issue.
            If taken   → removed from queue, continue next run.

Progress is tracked: queue.txt shrinks on every run.
"""

import itertools
import os
import random
import string
import time
import requests

# ── config ──────────────────────────────────────────────────────────────────
TOKEN       = os.environ["DISCORD_TOKEN"]
CHARS       = string.ascii_lowercase + string.digits   # a-z + 0-9  →  36 chars
NAME_LEN    = 3                                         # 36³ = 46,656 combos
MAX_TRIES   = 2                                         # Discord ≈ 2 changes/hour
QUEUE_FILE  = "queue.txt"
CLAIMED_FILE= "claimed.txt"
API_URL     = "https://discord.com/api/v10/users/@me"
# ────────────────────────────────────────────────────────────────────────────


# ── queue helpers ────────────────────────────────────────────────────────────

def build_queue() -> list[str]:
    """Generate every possible 3-char combo, shuffle once."""
    all_names = ["".join(c) for c in itertools.product(CHARS, repeat=NAME_LEN)]
    random.shuffle(all_names)
    print(f"Queue built: {len(all_names):,} names to try.")
    return all_names


def load_queue() -> list[str]:
    if not os.path.exists(QUEUE_FILE):
        return build_queue()
    with open(QUEUE_FILE) as f:
        return [line.strip() for line in f if line.strip()]


def save_queue(queue: list[str]) -> None:
    with open(QUEUE_FILE, "w") as f:
        f.write("\n".join(queue) + "\n")


# ── discord ──────────────────────────────────────────────────────────────────

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


# ── github actions output ────────────────────────────────────────────────────

def set_output(key: str, value: str) -> None:
    gha = os.environ.get("GITHUB_OUTPUT")
    if gha:
        with open(gha, "a") as f:
            f.write(f"{key}={value}\n")


# ── main ─────────────────────────────────────────────────────────────────────

def main() -> None:
    # Stop immediately if already claimed in a previous run
    if os.path.exists(CLAIMED_FILE):
        with open(CLAIMED_FILE) as f:
            name = f.read().strip()
        print(f"Already claimed: {name} — nothing to do.")
        set_output("claimed", name)
        return

    queue = load_queue()
    total = 36 ** NAME_LEN          # 46,656
    remaining = len(queue)
    tried_so_far = total - remaining
    pct = tried_so_far / total * 100
    print(f"Progress: {tried_so_far:,} / {total:,} tried ({pct:.1f}%) — {remaining:,} left in queue\n")

    for attempt in range(1, MAX_TRIES + 1):
        if not queue:
            print("Queue exhausted — all 46,656 names have been tried.")
            set_output("claimed", "")
            return

        name = queue.pop(0)         # take next from front of shuffled queue
        print(f"[{attempt}/{MAX_TRIES}] Trying → {name!r}")

        status, data = try_claim(name)

        # ── claimed! ──────────────────────────────────────────────────────
        if status == 200:
            claimed = data.get("username", name)
            print(f"\n🎉  SUCCESS — username claimed: {claimed}")
            with open(CLAIMED_FILE, "w") as f:
                f.write(claimed)
            set_output("claimed", claimed)
            save_queue(queue)       # save remaining queue (not needed again, but keep tidy)
            return

        # ── taken ─────────────────────────────────────────────────────────
        elif status == 400:
            body = str(data).lower()
            if "taken" in body or "already" in body:
                print(f"  ✗ Taken")
            else:
                errs = data.get("errors", data)
                print(f"  ✗ Rejected: {errs}")

        # ── rate limited ──────────────────────────────────────────────────
        elif status == 429:
            retry_after = data.get("retry_after", 3600)
            print(f"  ⏳ Rate limited — retry after {retry_after:.0f}s. Stopping.")
            queue.insert(0, name)   # put it back; wasn't actually tried
            save_queue(queue)
            set_output("claimed", "")
            return

        # ── auth error ────────────────────────────────────────────────────
        elif status in (401, 403):
            print(f"  🔑 Auth error {status} — check DISCORD_TOKEN secret.")
            queue.insert(0, name)
            save_queue(queue)
            set_output("claimed", "")
            return

        # ── other ─────────────────────────────────────────────────────────
        else:
            print(f"  ? Unexpected {status}: {data}")

        if attempt < MAX_TRIES:
            time.sleep(3)

    set_output("claimed", "")
    save_queue(queue)
    remaining_after = len(queue)
    print(f"\nRun done. Queue remaining: {remaining_after:,} / {total:,}")


if __name__ == "__main__":
    main()
