<div align="center">

# daily-trend-viewer

**A local website that shows popular YouTube, Shorts, Instagram Reels, X, Threads and TikTok content plus AI video news on one screen — no API key and no extra packages.**

[English](README.md) · [한국어](README.ko.md) · [日本語](README.ja.md) · [简体中文](README.zh-CN.md)

</div>

> Part of [AI Feature Pack](../../README.md) — packs are independent; install only what you need.

## What it does

- Filters popular YouTube videos and Shorts by category × period (today · this week · this month) and sorts them by views or likes. Click a card to play it in a popup.
- Searches YouTube for any keyword from the search box in the header and sorts the results by views.
- The AI video tab shows new and trending video-generation models (Hugging Face) and AI video news from Korea and abroad (Google News RSS).
- The Reels, X, Threads and TikTok tabs collect the latest posts of the accounts you follow. You add and remove accounts on screen.
- Results are cached for 1 hour. The refresh button at the top right updates them at once.
- Uses only the Python standard library. The server listens on `127.0.0.1` only.

## Quick start

```bash
# from the repo root
cd feature-pack/daily-trend-viewer/app
python3 server.py
# open http://localhost:28088 in your browser · stop with Ctrl+C
```

## Install

To let your agent do it, say "Read `feature-pack/daily-trend-viewer/INSTALL.md` and install it".

Manual steps: you only need Python 3.8 or later. The `app/` folder is the whole app, so you can copy it anywhere or run it where it is. If port 28088 is already in use, change `PORT = 28088` at the top of `app/server.py` to a free port.

```bash
# macOS: double-click app/실행-Mac.command (if Gatekeeper warns, right-click → Open), or
cd app && python3 server.py
# Windows: double-click app\실행-Windows.bat
# check — 200 means it works
curl -s -o /dev/null -w "%{http_code}" http://localhost:28088/
```

## Usage

### Tabs

| Tab | What you see | Sort by |
|---|---|---|
| YouTube / Shorts | Category (All · AI · mukbang · beauty · vlog · entertainment · movies/dramas · tech · knowledge · travel · animals) × period | views · likes |
| AI video | New video-generation models · trending models · AI video news (mostly text) | — |
| Reels | Latest Reels of the accounts you follow | views · likes · comments |
| X | Latest posts of the accounts you follow | likes · replies · retweets |
| Threads | Latest posts of the accounts you follow (account links when blocked) | likes · replies · reposts |
| TikTok | Live popular feed (Korea) + latest videos of the accounts you follow | views · likes · comments |

Popular AI videos are in the "AI" category of the YouTube tab. A search switches to the video tab; clicking a category clears the search.

### Account lists

When you change accounts on screen, these files are created in `app/`. Copy them too when you back up or move the app.

| Tab | File |
|---|---|
| Reels | `reels_accounts.json` |
| X | `x_accounts.json` |
| Threads | `threads_accounts.json` |
| TikTok | `tiktok_accounts.json` |

### Data sources and limits

- YouTube: calls the internal search API (InnerTube) sorted by views. YouTube's public trending feed was removed in 2025, so the app is built on search.
- Reels: calls the internal API used by the instagram.com website without login. Up to the latest 12 posts per account. Instagram may block for a while if requests come too often. Thumbnails go through the server proxy (`/api/img`).
- X: calls the syndication API used by the embed widget without login. This API has no view counts, so there is no sort by views.
- Threads: blocked by default for now, so it falls back to account links. Put a valid doc_id in `THREADS_DOC_IDS` in `server.py` to get live results.
- TikTok: goes through tikwm, a free public API (`www.tikwm.com/api`). Because it is a free tier, the server calls it with low concurrency (3) and caches for 1 hour.

### Good to know

- TikTok requests (account handles · what you look up) are sent to tikwm.com, a third-party service. If that service changes, the TikTok tab can stop at any time.
- All platform data comes from unofficial, unauthenticated internal APIs. This is a gray area under each service's terms and can be blocked without notice. Use it for personal viewing only and avoid refreshing too often.
- The `server.py` in this pack has 2 security patches over the original: Origin check on the account-change POST, and a stricter host check in the image proxy.

## Requirements

- macOS or Windows
- Python 3.8 or later (standard library only · no extra packages)
- API keys / accounts: none
- Install time: under 1 minute

## Links

- [INSTALL.md](INSTALL.md)
- [test/verify.md](test/verify.md) — detailed checks
- [Original release post](https://www.threads.com/@xazinga/post/DadL9WQD9ex)
- [AI Feature Pack catalog](../../README.md)
