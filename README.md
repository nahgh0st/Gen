# discord-username-hunter

Automatically hunts for available 3–4 character Discord usernames using GitHub Actions.

## How it works

Every 6 hours (or on manual trigger), the workflow:
1. Generates random 3–4 char candidates from `[a-z0-9]`
2. Tries to claim each via `PATCH /api/v10/users/@me`
3. Discord returns `200` → username is now yours → a GitHub Issue is opened to notify you
4. Discord returns `400` (taken) → logs it, moves to next candidate
5. All attempted names are saved to `tried.txt` and committed back, so runs never repeat

---

## Setup (5 minutes)

### 1. Fork / create this repo on GitHub

### 2. Add your Discord token as a secret

Go to **Settings → Secrets and variables → Actions → New repository secret**

| Name | Value |
|------|-------|
| `DISCORD_TOKEN` | your Discord user token |

**How to get your Discord token:**
1. Open Discord in a browser (discord.com/app)
2. Open DevTools → Network tab
3. Click any channel or action
4. Find any request to `discord.com/api` → look at the `Authorization` header
5. That value is your token — keep it private!

> ⚠️ Never commit your token to the repo. Use the GitHub Secret only.

### 3. Enable Actions

Go to the **Actions** tab in your repo and enable workflows if prompted.

### 4. Run manually first

Actions → **Discord Username Hunter** → **Run workflow** — watch the logs.

---

## Configuration (hunt.py)

| Variable | Default | Description |
|----------|---------|-------------|
| `CHARS` | `a-z0-9` | Characters used to build names |
| `LENGTHS` | `[4,4,4,3]` | Pick pool — skewed toward 4-char |
| `MAX_TRIES` | `2` | Attempts per run (respect rate limits) |

Change `LENGTHS = [3, 3, 3, 4]` to hunt more 3-char names (rarer, mostly taken).

---

## Rate limits

Discord allows roughly **2 username changes per hour** per account. The workflow is capped at 2 attempts per run and runs every 6 hours — well within that limit.

---

## Files

```
.github/workflows/username_hunter.yml   — the Actions workflow
hunt.py                                 — the hunter script
tried.txt                               — names already attempted (auto-updated)
```
